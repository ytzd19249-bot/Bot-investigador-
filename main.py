# main.py — BOT INVESTIGADOR (versión final lista para Render)
# Ejecuta: investigación (INVESTIGATION_MINUTES), afiliación (AFFILIATION_MINUTES) y envío cada SCHEDULE_CRON_HOURS (por defecto 12h).
# También permite ejecución manual POST /debug/run

import os
import asyncio
import time
from typing import List, Dict, Any
from datetime import datetime, timezone
import httpx
from fastapi import FastAPI, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler

app = FastAPI(title="Bot Investigador - Versión Final", version="2.0")

# -----------------------
# ENV / CONFIG
# -----------------------
SALES_PUBLIC_URL = os.getenv("SALES_PUBLIC_URL", "https://vendedorbt.onrender.com")
SALES_ADMIN_TOKEN = os.getenv("SALES_ADMIN_TOKEN", "ventas_admin_12345")

HOTMART_TOKEN = os.getenv("HOTMART_TOKEN")  # Bearer token Hotmart (requerido para Hotmart real)
HOTMART_CLIENT_ID = os.getenv("HOTMART_CLIENT_ID")  # para parámetros de afiliación si aplica

AMAZON_PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG")  # partner tag para Amazon
RAINFOREST_API_KEY = os.getenv("RAINFOREST_API_KEY")  # opcional: proxy Rainforest (para buscar bestsellers)

# Duraciones (minutos)
INVESTIGATION_MINUTES = int(os.getenv("INVESTIGATION_MINUTES", "60"))
AFFILIATION_MINUTES = int(os.getenv("AFFILIATION_MINUTES", "30"))
SCHEDULE_CRON_HOURS = int(os.getenv("SCHEDULE_CRON_HOURS", "12"))
MAX_PRODUCTS_PER_RUN = int(os.getenv("MAX_PRODUCTS_PER_RUN", "200"))

print(f"[INVESTIGADOR] Config: INVESTIGATION={INVESTIGATION_MINUTES}min AFFILIATION={AFFILIATION_MINUTES}min SCHEDULE_HOURS={SCHEDULE_CRON_HOURS} max_products={MAX_PRODUCTS_PER_RUN}")

# -----------------------
# UTIL
# -----------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def unique_by_key(items: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for it in items:
        k = it.get(key)
        if k and k not in seen:
            seen.add(k)
            out.append(it)
    return out

# -----------------------
# FUENTES: HOTMART, AMAZON (RAINFOREST), MERCADOLIBRE
# -----------------------
async def fetch_hotmart_products(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """
    Intenta obtener productos desde Hotmart usando HOTMART_TOKEN.
    Nota: Hotmart típicamente requiere permisos específicos; aquí intentamos un endpoint estándar.
    """
    out = []
    if not HOTMART_TOKEN:
        return out
    try:
        url = "https://api.hotmart.com/core/v1/products"  # endpoint genérico; ajustar según acceso Hotmart
        headers = {"Authorization": f"Bearer {HOTMART_TOKEN}"}
        r = await client.get(url, headers=headers, timeout=20.0)
        if r.status_code == 200:
            data = r.json()
            # Hotmart devuelve estructuras diversas; buscamos "items" o "products"
            items = data.get("items") or data.get("products") or data.get("data") or []
            for it in items[:100]:
                titulo = it.get("title") or it.get("name") or it.get("productName")
                precio = 0.0
                # hotmart puede no exponer precio directo, intentar campos comunes
                price_field = it.get("price") or it.get("price_amount") or (it.get("pricing") or {}).get("price")
                try:
                    precio = float(price_field or 0)
                except Exception:
                    precio = 0.0
                link = it.get("affiliate_link") or it.get("url") or it.get("landingPage") or it.get("link") or "#"
                out.append({
                    "titulo": str(titulo).strip() if titulo else None,
                    "precio": precio,
                    "categoria": it.get("category") or "Digital",
                    "link_afiliado": link
                })
    except Exception as e:
        print(f"[HOTMART] Error: {e}")
    return [p for p in out if p.get("titulo")]

async def fetch_amazon_via_rainforest(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """
    Rainforest API (o similar) como proxy para Amazon. Requiere RAINFOREST_API_KEY.
    Si no tiene key, no se ejecuta.
    """
    out = []
    if not RAINFOREST_API_KEY:
        return out
    try:
        # Pedimos bestsellers por categoría general (ejemplo)
        url = "https://api.rainforestapi.com/request"
        params = {"api_key": RAINFOREST_API_KEY, "type": "best_sellers", "amazon_domain": "amazon.com", "category_id": "16225007011"}  # ejemplo category
        r = await client.get(url, params=params, timeout=25.0)
        if r.status_code == 200:
            data = r.json()
            items = data.get("best_sellers") or data.get("search_results") or data.get("results") or []
            for it in items[:80]:
                titulo = it.get("title") or it.get("name")
                precio = 0.0
                try:
                    precio = float(it.get("price") or 0)
                except Exception:
                    precio = 0.0
                link = it.get("link") or it.get("url") or it.get("detail_page_url") or "#"
                out.append({
                    "titulo": str(titulo).strip() if titulo else None,
                    "precio": precio,
                    "categoria": it.get("category") or "Amazon",
                    "link_afiliado": link
                })
    except Exception as e:
        print(f"[AMAZON] Rainforest error: {e}")
    return [p for p in out if p.get("titulo")]

async def fetch_mercadolibre_trending(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    out = []
    try:
        r = await client.get("https://api.mercadolibre.com/sites/MLA/search?q=ofertas", timeout=15.0)
        if r.status_code == 200:
            data = r.json()
            for it in (data.get("results") or [])[:50]:
                titulo = it.get("title")
                precio = 0.0
                try:
                    precio = float(it.get("price") or 0)
                except Exception:
                    precio = 0.0
                link = it.get("permalink") or "#"
                out.append({
                    "titulo": titulo,
                    "precio": precio,
                    "categoria": it.get("category_id") or "ML",
                    "link_afiliado": link
                })
    except Exception as e:
        print(f"[MERCADOLIBRE] Error: {e}")
    return [p for p in out if p.get("titulo")]

# -----------------------
# INVESTIGACIÓN PRINCIPAL (durante duration_minutes)
# -----------------------
async def investigate_for_duration(duration_minutes: int) -> List[Dict[str, Any]]:
    start = time.time()
    deadline = start + duration_minutes * 60
    collected: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        iteration = 0
        while time.time() < deadline and len(collected) < MAX_PRODUCTS_PER_RUN:
            iteration += 1
            print(f"[INVESTIGADOR] iter {iteration} - {now_iso()} - collected {len(collected)}")
            tasks = [
                fetch_hotmart_products(client),
                fetch_amazon_via_rainforest(client),
                fetch_mercadolibre_trending(client)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    print(f"[INVESTIGADOR] fuente falló: {res}")
                    continue
                for p in (res or []):
                    if not p.get("titulo"):
                        continue
                    producto = {
                        "titulo": str(p.get("titulo")).strip(),
                        "precio": float(p.get("precio") or 0),
                        "categoria": str(p.get("categoria") or "General"),
                        "link_afiliado": str(p.get("link_afiliado") or "#")
                    }
                    collected.append(producto)
            collected = unique_by_key(collected, "titulo")
            await asyncio.sleep(6)  # iteraciones más rápidas para recolectar más en la ventana
    print(f"[INVESTIGADOR] Investigación finalizada. Recolectados: {len(collected)}")
    return collected[:MAX_PRODUCTS_PER_RUN]

# -----------------------
# AFILIACIÓN
# -----------------------
async def try_affiliate_hotmart(product: Dict[str, Any]) -> Dict[str, Any]:
    link = product.get("link_afiliado") or "#"
    if "hotmart" in link.lower() and HOTMART_TOKEN:
        # Añadimos client_id como parámetro de afiliación simple si aplica
        sep = "&" if "?" in link else "?"
        product["link_afiliado"] = link + f"{sep}affiliate={HOTMART_CLIENT_ID or 'auto'}"
        product["_afiliado_por"] = "hotmart"
        return product
    return product

async def try_affiliate_amazon(product: Dict[str, Any]) -> Dict[str, Any]:
    link = product.get("link_afiliado") or "#"
    if "amazon." in link.lower() and AMAZON_PARTNER_TAG:
        if "tag=" not in link and "partnerTag=" not in link:
            sep = "&" if "?" in link else "?"
            product["link_afiliado"] = link + f"{sep}tag={AMAZON_PARTNER_TAG}"
            product["_afiliado_por"] = "amazon"
            return product
    return product

async def affiliation_phase(products: List[Dict[str, Any]], duration_minutes: int) -> List[Dict[str, Any]]:
    start = time.time()
    deadline = start + duration_minutes * 60
    approved: List[Dict[str, Any]] = []
    i = 0
    total = len(products)
    while time.time() < deadline and i < total:
        p = products[i]
        try:
            p = await try_affiliate_hotmart(p)
            p = await try_affiliate_amazon(p)
            if p.get("link_afiliado") and p.get("link_afiliado") != "#":
                approved.append(p)
        except Exception as e:
            print(f"[AFILIACION] Error en '{p.get('titulo')}': {e}")
        i += 1
    approved = unique_by_key(approved, "titulo")
    print(f"[AFILIACION] Aprobados: {len(approved)} / {len(products)}")
    return approved

# -----------------------
# ENVÍO A BOT VENTAS
# -----------------------
async def send_to_sales(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    sales_url = SALES_PUBLIC_URL.rstrip("/") + "/ingestion/productos"
    headers = {"Authorization": f"Bearer {SALES_ADMIN_TOKEN}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.post(sales_url, json={"productos": products}, headers=headers)
            try:
                j = res.json()
            except Exception:
                j = {"status_code": res.status_code, "text": res.text}
            print(f"[INVESTIGADOR] Envío a ventas HTTP {res.status_code} -> {j}")
            return {"status": res.status_code, "response": j}
        except Exception as e:
            print(f"[INVESTIGADOR] Error enviando a ventas: {e}")
            return {"error": str(e)}

# -----------------------
# RUN EXTENDIDO (investiga + afilia + envía)
# -----------------------
async def run_research_extended() -> Dict[str, Any]:
    started = now_iso()
    print(f"[INVESTIGADOR] >>> INICIO CORRIDA EXTENDIDA {started}")
    products = await investigate_for_duration(INVESTIGATION_MINUTES)
    if not products:
        print("[INVESTIGADOR] No se encontraron productos en investigación.")
        return {"ok": True, "sent_to": SALES_PUBLIC_URL, "productos_enviados": 0, "reason": "no_products_found"}
    approved = await affiliation_phase(products, AFFILIATION_MINUTES)
    if not approved:
        print("[INVESTIGADOR] No se afiliaron productos.")
        return {"ok": True, "sent_to": SALES_PUBLIC_URL, "productos_enviados": 0, "reason": "no_affiliates"}
    result = await send_to_sales(approved)
    finished = now_iso()
    print(f"[INVESTIGADOR] >>> FIN CORRIDA EXTENDIDA {finished}")
    return {
        "ok": True,
        "started": started,
        "finished": finished,
        "found": len(products),
        "approved": len(approved),
        "sales_result": result
    }

# -----------------------
# RUTAS
# -----------------------
@app.get("/")
async def home():
    return {"ok": True, "bot": "investigador", "status": "activo", "time": now_iso()}

@app.post("/debug/run")
async def debug_run(request: Request):
    """
    Ejecuta manualmente la investigación extendida.
    POST {} o POST {"run": true}
    """
    print("[INVESTIGADOR] 🧠 Ejecución manual solicitada (extendida)")
    asyncio.create_task(run_research_extended())
    return {"ok": True, "message": "Investigación extendida iniciada (background)."}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    _ = await request.json()
    return {"ok": True}

# -----------------------
# SCHEDULER
# -----------------------
scheduler = AsyncIOScheduler(timezone="America/Costa_Rica")

@scheduler.scheduled_job("interval", hours=SCHEDULE_CRON_HOURS)
async def scheduled_research_job():
    print(f"[INVESTIGADOR] ⏰ Scheduler triggered at {now_iso()}")
    asyncio.create_task(run_research_extended())

@app.on_event("startup")
async def startup_event():
    print("[INVESTIGADOR] 🚀 Bot investigador iniciado correctamente.")
    scheduler.start()
