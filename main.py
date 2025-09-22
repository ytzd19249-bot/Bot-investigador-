import os
import time
import math
import logging
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError

# -------------------- LOGGING --------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot-investigador")

# -------------------- CONFIG --------------------
DATABASE_URL = os.getenv("DATABASE_URL")
HOT_BASE = os.getenv("HOTMART_API_BASE", "https://api.hotmart.com")
CLIENT_ID = os.getenv("HOTMART_CLIENT_ID")
CLIENT_SECRET = os.getenv("HOTMART_CLIENT_SECRET")
INTERVAL = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "60"))
TOP_K = int(os.getenv("TOP_K_PRODUCTS", "10"))
AFFILIATE_AUTO = os.getenv("AFFILIATION_AUTO_APPROVE", "true").lower() in ("1","true","yes")

if not DATABASE_URL:
    raise RuntimeError("Set DATABASE_URL env var")

# -------------------- DB --------------------
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True)
    nombre = Column(String(512))
    categoria = Column(String(255), index=True)
    precio = Column(Float, nullable=True)
    comision = Column(String(50), nullable=True)
    link_afiliado = Column(Text, nullable=True)
    imagen_url = Column(Text, nullable=True)
    descripcion = Column(Text, nullable=True)
    fuente = Column(String(50), index=True)
    score = Column(Float, default=0.0)
    afiliado = Column(Boolean, default=False)
    fecha_detectado = Column(DateTime(timezone=True), server_default=func.now())

Base.metadata.create_all(bind=engine)

# -------------------- HOTMART API --------------------
_cached = {"token": None, "expires_at": 0}

def get_hotmart_token():
    now = int(time.time())
    if _cached["token"] and _cached["expires_at"] > now + 10:
        return _cached["token"]

    token_url = f"{HOT_BASE}/oauth/token"  # ⚠️ ajustar según docs Hotmart
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    resp = requests.post(token_url, data=data, timeout=15)
    resp.raise_for_status()
    j = resp.json()
    access = j.get("access_token")
    expires_in = j.get("expires_in", 3600)
    _cached["token"] = access
    _cached["expires_at"] = int(time.time()) + int(expires_in)
    return access

def list_hotmart_products(page=1, per_page=50):
    token = get_hotmart_token()
    url = f"{HOT_BASE}/marketplace/v1/products?page={page}&limit={per_page}"  # ⚠️ ajustar endpoint real
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def request_affiliation(product_id):
    token = get_hotmart_token()
    url = f"{HOT_BASE}/affiliate/v1/requests"  # ⚠️ ajustar según docs Hotmart
    payload = {"product_id": product_id}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=20)
    return r.status_code, r.json() if r.content else {}

# -------------------- LOGICA --------------------
def score_product(raw):
    sales = float(raw.get("sales", 0))
    rating = float(raw.get("rating", 0))
    trending = float(raw.get("trending_score", 0))
    score = math.log1p(sales) * 0.6 + rating * 0.3 + trending * 0.1
    return score

def process_hotmart_page(page=1):
    logger.info("Consultando Hotmart - page %s", page)
    try:
        data = list_hotmart_products(page=page, per_page=50)
    except Exception as e:
        logger.exception("Error consultando Hotmart: %s", e)
        return []

    items = data.get("items") or data.get("products") or []
    processed = []
    for it in items:
        external_id = str(it.get("id") or it.get("productId") or it.get("externalId"))
        nombre = it.get("title") or it.get("name") or "Sin nombre"
        categoria = it.get("category") or it.get("categoryName") or "General"
        precio = float(it.get("price", 0) or 0)
        comision = str(it.get("commission", ""))
        descripcion = it.get("description", "")[:3000]
        imagen = it.get("image") or it.get("thumbnail")
        sales = it.get("sales") or it.get("soldQuantity") or 0
        trending_score = it.get("trending_score", 0)
        rating = it.get("rating", 0)

        raw = {"sales": sales, "rating": rating, "trending_score": trending_score}
        score = score_product(raw)

        processed.append({
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
        })
    return processed

def run_cycle():
    logger.info("=== Ciclo investigador START ===")
    all_candidates = []
    for p in range(1, 4):
        items = process_hotmart_page(page=p)
        all_candidates.extend(items)

    all_candidates.sort(key=lambda x: x["score"], reverse=True)
    top = all_candidates[:TOP_K]
    logger.info("Top %s candidatos listos (total encontrados %s)", TOP_K, len(all_candidates))

    db = SessionLocal()
    for item in top:
        try:
            prod = db.query(Producto).filter(Producto.external_id==item["external_id"]).first()
            if not prod:
                prod = Producto(
                    external_id=item["external_id"],
                    nombre=item["nombre"],
                    categoria=item["categoria"],
                    precio=item["precio"],
                    comision=item["comision"],
                    descripcion=item["descripcion"],
                    imagen_url=item["imagen"],
                    fuente=item["fuente"],
                    score=item["score"],
                    afiliado=False
                )
                db.add(prod)
                db.commit()
                logger.info("Guardado producto: %s (score=%.2f)", item["nombre"], item["score"])
            else:
                prod.score = item["score"]
                db.commit()
        except IntegrityError:
            db.rollback()
        except Exception:
            db.rollback()
            logger.exception("Error guardando producto")

        if AFFILIATE_AUTO:
            try:
                if not prod.afiliado:
                    status_code, resp = request_affiliation(prod.external_id)
                    logger.info("Solicitud afiliación %s -> %s", prod.external_id, status_code)
                    if status_code in (200,201):
                        prod.afiliado = True
                        link = resp.get("affiliate_link") or resp.get("affiliateUrl")
                        if link:
                            prod.link_afiliado = link
                        db.commit()
            except Exception:
                logger.exception("Error en afiliación automática para %s", prod.external_id)

    db.close()
    logger.info("=== Ciclo investigador END ===")

# -------------------- MAIN --------------------
if __name__ == "__main__":
    run_cycle()
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_cycle, 'interval', minutes=INTERVAL, next_run_time=None)
    scheduler.start()
    logger.info("Scheduler iniciado, interval: %s min", INTERVAL)

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
