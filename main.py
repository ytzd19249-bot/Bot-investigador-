# main.py
import os
import time
import math
import logging
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, HTTPException
from sqlalchemy.exc import IntegrityError

from db import init_db, SessionLocal, Producto
import hotmart_api

# -------------------- logging --------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("investigador")

# -------------------- config desde ENV --------------------
DATABASE_URL = os.getenv("DATABASE_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")                # opcional: para notificar admin en Telegram
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")                  # opcional: chat id del admin para notificaciones
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")                  # token simple para endpoints admin (poner uno seguro)
SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "60"))
TOP_K_PRODUCTS = int(os.getenv("TOP_K_PRODUCTS", "10"))
PAGES_TO_SCAN = int(os.getenv("PAGES_TO_SCAN", "3"))        # cuántas páginas leer por ciclo
AFFILIATE_AUTO = os.getenv("AFFILIATION_AUTO_APPROVE", "true").lower() in ("1","true","yes")

# -------------------- init db --------------------
if not DATABASE_URL:
    raise RuntimeError("Set DATABASE_URL env var in Render")

init_db()
app = FastAPI()

# -------------------- util Telegram --------------------
def send_telegram(text: str, chat_id: str = None):
    if not TELEGRAM_TOKEN or not (chat_id or ADMIN_CHAT_ID):
        logger.debug("Telegram no configurado; no envío notificación")
        return
    cid = chat_id or ADMIN_CHAT_ID
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": cid, "text": text, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.exception("Error enviando telegram: %s", e)

# -------------------- scoring simple (reemplazable por GPT-R) --------------------
def score_product(raw: dict) -> float:
    """
    Heurística simple que prioriza ventas + trending + rating.
    raw puede tener keys: 'sales', 'rating', 'trending_score' (depende Hotmart).
    """
    try:
        sales = float(raw.get("sales", 0) or 0)
        rating = float(raw.get("rating", 0) or 0)
        trending = float(raw.get("trending_score", 0) or 0)
    except Exception:
        sales, rating, trending = 0.0, 0.0, 0.0
    # combinar en score
    score = math.log1p(sales) * 0.65 + rating * 0.25 + trending * 0.10
    return float(score)

# -------------------- procesar y guardar candidatos --------------------
def process_candidates(candidates: list):
    db = SessionLocal()
    saved = 0
    for item in candidates:
        try:
            external_id = item.get("external_id") or str(item.get("id") or item.get("productId") or "")
            if not external_id:
                continue
            # verificar si ya existe
            prod = db.query(Producto).filter(Producto.external_id == external_id).first()
            if not prod:
                prod = Producto(
                    external_id=external_id,
                    nombre=item.get("nombre") or item.get("title") or "Sin nombre",
                    categoria=item.get("categoria") or item.get("category") or "General",
                    precio=float(item.get("precio") or item.get("price") or 0.0),
                    comision=str(item.get("comision") or item.get("commission") or ""),
                    descripcion=(item.get("descripcion") or item.get("description") or "")[:3000],
                    imagen_url=item.get("imagen") or item.get("image") or None,
                    fuente=item.get("fuente") or "hotmart",
                    score=float(item.get("score") or 0.0),
                    afiliado=False,
                )
                db.add(prod)
                db.commit()
                saved += 1
                logger.info("Guardado producto: %s (score=%.2f)", prod.nombre, prod.score)
            else:
                # actualizar score si cambió
                new_score = float(item.get("score") or 0.0)
                if abs((prod.score or 0.0) - new_score) > 0.01:
                    prod.score = new_score
                    db.commit()
        except IntegrityError:
            db.rollback()
        except Exception:
            db.rollback()
            logger.exception("Error guardando producto")
            continue

        # intentar afiliación automática si corresponde y aún no afiliado
        try:
            if AFFILIATE_AUTO:
                prod = db.query(Producto).filter(Producto.external_id == external_id).first()
                if prod and not prod.afiliado:
                    status_code, resp = hotmart_api.request_affiliation(prod.external_id)
                    logger.info("Affiliation request for %s -> %s", prod.external_id, status_code)
                    # manejar respuesta según doc real
                    if status_code in (200, 201):
                        prod.afiliado = True
                        link = resp.get("affiliate_link") or resp.get("affiliateUrl") or resp.get("affiliate_url")
                        if link:
                            prod.link_afiliado = link
                        db.commit()
        except Exception:
            logger.exception("Error en intento de afiliación automática")

    db.close()
    return saved

# -------------------- ciclo investigador --------------------
def run_cycle():
    logger.info("=== Ciclo investigador START ===")
    all_candidates = []
    try:
        for p in range(1, PAGES_TO_SCAN + 1):
            raw_items = hotmart_api.list_hotmart_products(page=p, per_page=50)
            # adaptar dependiendo de la estructura que devuelva Hotmart
            items = raw_items.get("items") or raw_items.get("products") or raw_items.get("data") or []
            for it in items:
                # extraer campos robustamente
                external_id = str(it.get("id") or it.get("productId") or it.get("externalId") or "")
                nombre = it.get("title") or it.get("name") or it.get("productName") or "Sin nombre"
                categoria = it.get("category") or it.get("categoryName") or "General"
                precio = float(it.get("price", {}).get("value", 0) if isinstance(it.get("price", {}), dict) else (it.get("price") or 0))
                comision = it.get("commission") or it.get("comission") or ""
                descripcion = it.get("description") or it.get("shortDescription") or ""
                imagen = (it.get("image") or it.get("thumbnail") or "")
                # heurística fields
                sales = it.get("sales") or it.get("soldQuantity") or it.get("salesCount") or 0
                rating = it.get("rating") or it.get("averageRating") or 0
                trending_score = it.get("trending_score") or it.get("trend") or 0

                raw = {"sales": sales, "rating": rating, "trending_score": trending_score}
                score = score_product(raw)

                candidate = {
                    "external_id": external_id,
                    "nombre": nombre,
                    "categoria": categoria,
                    "precio": precio,
                    "comision": comision,
                    "descripcion": descripcion,
                    "imagen": imagen,
                    "fuente": "hotmart",
                    "score": score,
                    "raw": it
                }
                all_candidates.append(candidate)
    except Exception:
        logger.exception("Error durante consulta Hotmart")

    # ordenar por score y tomar top K
    all_candidates.sort(key=lambda x: x["score"], reverse=True)
    top = all_candidates[:TOP_K_PRODUCTS]
    logger.info("Top candidatos: %s (de %s encontrados)", len(top), len(all_candidates))

    saved = process_candidates(top)
    logger.info("Guardados en DB: %s productos", saved)
    if saved > 0:
        send_telegram(f"✅ Investigador guardó {saved} productos nuevos.", None)
    logger.info("=== Ciclo investigador END ===")

# -------------------- scheduler --------------------
scheduler = BackgroundScheduler()
scheduler.add_job(run_cycle, "interval", minutes=SCRAPE_INTERVAL_MINUTES, next_run_time=None)
scheduler.start()
logger.info("Scheduler iniciado - interval: %s minutos", SCRAPE_INTERVAL_MINUTES)

# -------------------- FastAPI endpoints (health + admin) --------------------
@app.get("/health")
def health():
    return {"status": "ok", "message": "Investigador vivo"}

@app.post("/admin/run_now")
def admin_run_now(token: str = "", request: Request = None):
    # endpoint protegido por ADMIN_TOKEN
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    # lanzar un ciclo inmediato en background
    scheduler.add_job(run_cycle, "date", run_date=time.time() + 1)
    return {"ok": True, "msg": "Ciclo programado ahora"}

@app.get("/admin/status")
def admin_status(token: str = ""):
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"scheduler_running": True, "interval_minutes": SCRAPE_INTERVAL_MINUTES, "top_k": TOP_K_PRODUCTS}

# -------------------- startup webhook opcional (solo si quiere notificaciones por Telegram) --------------------
@app.on_event("startup")
def startup():
    # si quiere que el bot responda por Telegram en / (opcional)
    if TELEGRAM_TOKEN and os.getenv("WEBHOOK_URL"):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={os.getenv('WEBHOOK_URL')}"
            r = requests.get(url, timeout=10)
            logger.info("Webhook configurado: %s", r.json())
        except Exception:
            logger.exception("No se pudo configurar webhook (continuo igual)")

# -------------------- keep alive (cuando lo corra con python main.py) --------------------
if __name__ == "__main__":
    # correr un ciclo al inicio
    run_cycle()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Terminando...")
