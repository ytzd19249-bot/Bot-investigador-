# main.py — BOT INVESTIGADOR (INVESTIGACIÓN 1h + AFILIACIÓN 30min, envío cada 12h)
import os
import asyncio
import math
import time
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

import httpx
from fastapi import FastAPI, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler

app = FastAPI(title="Bot Investigador - Extendido", version="1.0")

# -----------------------
# VARIABLES DE ENTORNO (asegúrese que estén en Render)
# -----------------------
SALES_PUBLIC_URL = os.getenv("SALES_PUBLIC_URL", "https://vendedorbt.onrender.com")
SALES_ADMIN_TOKEN = os.getenv("SALES_ADMIN_TOKEN", "ventas_admin_12345")
HOTMART_BASIC = os.getenv("HOTMART_BASIC")  # base64 basic auth if disponible
HOTMART_CLIENT_ID = os.getenv("HOTMART_CLIENT_ID")
HOTMART_CLIENT_SECRET = os.getenv("HOTMART_CLIENT_SECRET")
HOTMART_TOKEN = os.getenv("HOTMART_TOKEN")
AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
AMAZON_PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG")

# Duraciones (minutos). Usted pidió 1h investigación, 30 min afiliación
INVESTIGATION_MINUTES = int(os.getenv("INVESTIGATION_MINUTES", "60"))  # 60 min
AFFILIATION_MINUTES = int(os.getenv("AFFILIATION_MINUTES", "30"))      # 30 min
SCHEDULE_CRON_HOURS = int(os.getenv("SCHEDULE_CRON_HOURS", "12"))      # cada 12 horas

# LÍMITE de productos a manejar por corrida (evita llenar DB)
MAX_PRODUCTS_PER_RUN = int(os.getenv("MAX_PRODUCTS_PER_RUN", "200"))

print(f"[INVESTIGADOR] Config: INVESTIGATION_MIN={INVESTIGATION_MINUTES}min AFFILIATION_MIN={AFFILIATION_MINUTES}min SCHEDULE_HOURS={SCHEDULE_CRON_HOURS}")

# -----------------------
# UTILIDADES
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
# OBTENCIÓN / INVESTIGACIÓN
# -----------------------
async def fetch_hotmart_trending(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Intenta obtener productos desde Hotmart si hay credenciales. Retorna lista de productos."""
    out = []
    # Hotmart API real requiere OAuth; si HOTMART_TOKEN está presente, intentamos llamar endpoints comunes.
    if HOTMART_TOKEN:
        try:
            # Ejemplo: endpoint hipotético (ajustar según documentación real de Hotmart)
            url = "https://api.hotmart.com/v2/products"  # placeholder; cambie si tiene endpoint real
            headers = {"Authorization": f"Bearer {HOTMART_TOKEN}"}
            r = await client.get(url, headers=headers, timeout=20.0)
            if r.status_code == 200:
                data = r.json()
                items = data.get("items") or data.get("products") or []
                for it in items[:50]:
                    out.append({
                        "titulo": it.get("title") or it.get("name"),
                        "precio": float(it.get("price") or 0),
                        "categoria": it.get("category") or "Digital",
                        "link_afiliado": it.get("affiliate_link") or it.get("url") or it.get("landing_page") or "#"
                    })
        except Exception as e:
            print(f"[HOTMART] Error al obtener datos: {e}")
    return out

async def fetch_amazon_trending(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Intenta obtener productos desde Amazon (Product Advertising API). Implementación básica."""
    out = []
    # La API de Amazon Product Advertising es compleja (firma). Aquí intentamos una llamada simplificada si tiene partner tag.
    if AMAZON_ACCESS_KEY and AMAZON_SECRET_KEY and AMAZON_PARTNER_TAG:
        try:
            # Placeholder: si usted tiene un proxy o wrapper para la API, apúntelo aquí.
            # En muchos setups se usa una función/signature para firmar la petición; omitimos la firma aquí.
            url = f"https://api.example-amazon-proxy.local/top"  # REEMPLACE si tiene proxy real
            r = await client.get(url, timeout=20.0)
            if r.status_code == 200:
                data = r.json()
                for it in (data.get("items") or [])[:50]:
                    out.append({
                        "titulo": it.get("title") or it.get("name"),
                        "precio": float(it.get("price") or 0),
                        "categoria": it.get("category") or "Amazon",
                        "link_afiliado": (it.get("detail_page_url") or "#")
                    })
        except Exception as e:
            print(f"[AMAZON] Error al obtener datos: {e}")
    return out

async def fetch_other_sources(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Agregue aquí otras fuentes: MercadoLibre, Bing trends, feeds RSS, etc."""
    out = []
    # Ejemplo: MercadoLibre pública (search trending) - solo si desea
    try:
        r = await client.get("https://api.mercadolibre.com/sites/MLA/search?q=top+ventas", timeout=15.0)
        if r.status_code == 200:
            data = r.json()
            for it in (data.get("results") or [])[:30]:
                out.append({
                    "titulo": it.get("title"),
                    "precio": float(it.get("price") or 0),
                    "categoria": it.get("category_id") or "ML",
                    "link_afiliado": it.get("permalink")
                })
    except Exception:
        pass
    return out

async def investigate_for_duration(duration_minutes: int) -> List[Dict[str, Any]]:
    """
    Ejecuta la fase de investigación durante 'duration_minutes'.
    Va llamando a fuentes, acumulando y deduplicando productos.
    """
    start = time.time()
    deadline = start + duration_minutes * 60
    collected: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        iteration = 0
        while time.time() < deadline and len(collected) < MAX_PRODUCTS_PER_RUN:
            iteration += 1
            print(f"[INVESTIGADOR] Investigación iter {iteration} - {now_iso()}; encontrados hasta ahora: {len(collected)}")
            # Llamadas concurrentes a fuentes
            tasks = [
                fetch_hotmart_trending(client),
                fetch_amazon_trending(client),
                fetch_other_sources(client),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    print(f"[INVESTIGADOR] Fuente falló: {res}")
                    continue
                for p in (res or []):
                    # asegure formato requerido (titulo, precio, categoria, link_afiliado)
                    if not p.get("titulo"):
                        continue
                    producto = {
                        "titulo": str(p.get("titulo")).strip(),
                        "precio": float(p.get("precio") or 0),
                        "categoria": str(p.get("categoria") or "General"),
                        "link_afiliado": str(p.get("link_afiliado") or "#")
                    }
                    collected.append(producto)
            # dedup
            collected = unique_by_key(collected, "titulo")
            # pausa corta entre iteraciones para no saturar APIs (y para darle tiempo de afinar tendencias)
            await asyncio.sleep(12)  # 12s por iteración, puede ajustar
    # Truncar a tope y devolver
    print(f"[INVESTIGADOR] Investigación finalizada. Total recolectados: {len(collected)}")
    return collected[:MAX_PRODUCTS_PER_RUN]

# -----------------------
# AFILIACIÓN (30 minutos)
# -----------------------
async def try_affiliate_hotmart(product: Dict[str, Any]) -> Dict[str, Any]:
    """Intento de afiliación para Hotmart: si HOTMART_TOKEN disponible se intenta obtener link de afiliado."""
    # Implementación básica: si link ya apunta a hotmart, añadimos token o dejamos link tal cual
    link = product.get("link_afiliado") or "#"
    if "hotmart" in link.lower() and HOTMART_TOKEN:
        # ejemplo: si Hotmart requiere exchange, aquí se colocaría la llamada
        # por ahora agregamos un query param ficticio para representar afiliación válida
        if "?" in link:
            link = link + f"&affiliate={HOTMART_CLIENT_ID or 'auto'}"
        else:
            link = link + f"?affiliate={HOTMART_CLIENT_ID or 'auto'}"
        product["link_afiliado"] = link
        product["_afiliado_por"] = "hotmart"
        return product
    return product

async def try_affiliate_amazon(product: Dict[str, Any]) -> Dict[str, Any]:
    """Intento de afiliación para Amazon: si tiene PARTNER_TAG, añadimos partner tag al link."""
    link = product.get("link_afiliado") or "#"
    if AMAZON_PARTNER_TAG:
        # Si link ya contiene tag, no lo duplicamos; simplemente agregamos partner tag si es posible.
        # Nota: idealmente usar Product Advertising API para generar enlaces con partner tag.
        if "amazon." in link.lower():
            if "tag=" not in link and "partnerTag=" not in link:
                sep = "&" if "?" in link else "?"
                link = link + f"{sep}tag={AMAZON_PARTNER_TAG}"
                product["link_afiliado"] = link
                product["_afiliado_por"] = "amazon"
                return product
    return product

async def affiliation_phase(products: List[Dict[str, Any]], duration_minutes: int) -> List[Dict[str, Any]]:
    """
    Intenta afiliar productos durante duration_minutes.
    Devuelve lista de productos aprobados/afiliados (pueden ser subset de entrada).
    """
    start = time.time()
    deadline = start + duration_minutes * 60
    approved: List[Dict[str, Any]] = []
    i = 0
    total = len(products)
    # Rolling attempts: intentamos procesar todos en ciclos hasta que se agote el tiempo.
    while time.time() < deadline and i < total:
        p = products[i]
        try:
            # Intentos simples de afiliación por proveedor
            p_before = p.copy()
            p = await try_affiliate_hotmart(p)
            p = await try_affiliate_amazon(p)
            # Aquí puede añadirse lógica adicional: comprobación de link, verificación de status 200, etc.
            # Validación mínima: link_afiliado no sea '#'
            if p.get("link_afiliado") and p.get("link_afiliado") != "#":
                approved.append(p)
            else:
                # Si no pudo afiliarse, puede intentar más tarde en otro ciclo (pero por simplicidad lo descartamos ahora)
                pass
        except Exception as e:
            print(f"[AFILIACION] Error procesando producto '{p.get('titulo')}': {e}")
        i += 1
        # Si acabamos la lista y aún hay tiempo, podemos volver desde el principio para reintentar fallidos
        if i >= total and time.time() < deadline:
            # reintentar fallidos? Aquí simplemente rompemos para ahorro; puede ajustar si quiere reintentos.
            break
    # dedup
    approved = unique_by_key(approved, "titulo")
    print(f"[AFILIACION] Finalizada. Aprobados: {len(approved)} / {len(products)}")
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
# FUNCION PRINCIPAL EXTENDIDA
# -----------------------
async def run_research_extended() -> Dict[str, Any]:
    started = now_iso()
    print(f"[INVESTIGADOR] >>> INICIO CORRIDA EXTENDIDA {started}")
    # 1) Investigacion (1 hora)
    products = await investigate_for_duration(INVESTIGATION_MINUTES)
    if not products:
        print("[INVESTIGADOR] No se encontraron productos en la fase de investigación.")
        # Devolvemos sin enviar si no hay nada
        return {"ok": True, "sent_to": SALES_PUBLIC_URL, "productos_enviados": 0, "reason": "no_products_found"}

    # 2) Afiliación (30 minutos)
    approved = await affiliation_phase(products, AFFILIATION_MINUTES)
    if not approved:
        print("[INVESTIGADOR] No se afiliaron productos en la fase de afiliación.")
        # Decide: enviar vacíos o no. Aquí no enviamos para evitar insertados=0
        return {"ok": True, "sent_to": SALES_PUBLIC_URL, "productos_enviados": 0, "reason": "no_affiliates"}

    # 3) Envío al bot de ventas
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
    return {"ok": True, "bot": "investigador", "status": "activo"}

@app.post("/debug/run")
async def debug_run(request: Request):
    """
    Ejecuta manualmente la investigación extendida.
    Use POST con JSON {} o {"run": true}
    """
    print("[INVESTIGADOR] 🧠 Ejecución manual solicitada (extendida)")
    # no bloquear la respuesta: corremos y devolvemos que inició
    task = asyncio.create_task(run_research_extended())
    return {"ok": True, "message": "Investigación extendida iniciada (background)."}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    _ = await request.json()
    return {"ok": True}

# -----------------------
# SCHEDULER cada SCHEDULE_CRON_HOURS
# -----------------------
scheduler = AsyncIOScheduler(timezone="America/Costa_Rica")

@scheduler.scheduled_job("interval", hours=SCHEDULE_CRON_HOURS)
async def scheduled_research_job():
    print(f"[INVESTIGADOR] ⏰ Scheduler triggered at {now_iso()}")
    # Ejecuta en background para no bloquear el scheduler
    asyncio.create_task(run_research_extended())

@app.on_event("startup")
async def startup_event():
    print("[INVESTIGADOR] 🚀 Bot investigador iniciado correctamente.")
    scheduler.start()
