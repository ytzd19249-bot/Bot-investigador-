# main.py
import os
import asyncio
from typing import Dict
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import httpx

from db import init_db, SessionLocal, Producto
import hotmart_api  # funciones: obtener_productos_hotmart(), afiliar_producto_hotmart()

# Inicializar app y DB
app = FastAPI(title="Bot Investigador - Hotmart")
init_db()

# ENV vars (configurar en Render)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")           # token del bot investigador (opcional, para /status)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "miclaveadmin") # token que usará para llamar /admin/update (bot de ventas)
PUBLIC_URL = os.getenv("PUBLIC_URL", "")               # ej: https://bot-investigador.onrender.com
HOTMART_BASIC = os.getenv("HOTMART_BASIC")            # Basic ... (client_id:client_secret codificado) o token
HOTMART_CLIENT_ID = os.getenv("HOTMART_CLIENT_ID")
HOTMART_CLIENT_SECRET = os.getenv("HOTMART_CLIENT_SECRET")
SCHEDULE_CRON_HOURS = int(os.getenv("SCHEDULE_CRON_HOURS", "12"))  # cada cuantas horas investigar

BASE_TELEGRAM = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None

# --- util: enviar mensaje telegram (opcional, para status) ---
async def send_telegram(chat_id: int, text: str):
    if not BASE_TELEGRAM:
        return None
    async with httpx.AsyncClient(timeout=15.0) as c:
        await c.post(f"{BASE_TELEGRAM}/sendMessage", json={"chat_id": chat_id, "text": text})

# --- función principal de investigación (puedes llamarla manual o por scheduler) ---
async def run_investigation_once():
    """Busca productos en Hotmart, filtra, se afilia y guarda en DB."""
    now = datetime.utcnow().isoformat()
    # 1) obtener listado candidates (hotmart_api se encarga del endpoint real)
    try:
        candidatos = hotmart_api.obtener_productos_hotmart(HOTMART_BASIC, limit=50)
    except Exception as e:
        print("Error al obtener productos Hotmart:", e)
        return {"ok": False, "error": str(e)}

    añadidos = 0
    db = SessionLocal()
    try:
        for p in candidatos:
            # p: dict con keys: title, price, currency, product_id, affiliate_available, link, etc.
            # Filtrar: solo afiliar si affiliate_available True (ejemplo)
            if not p.get("affiliate_available", True):
                continue

            # Intentar afiliar (hotmart_api debería retornar link afiliado)
            try:
                affiliate = hotmart_api.afiliar_producto_hotmart(HOTMART_BASIC, p["product_id"])
            except Exception as e:
                # si no se puede afiliar, saltar
                print("No se afilió:", p.get("product_id"), e)
                continue

            # Guardar o actualizar en DB (buscar por product_id o link)
            existing = db.query(Producto).filter(Producto.source_id == p.get("product_id")).first()
            if existing:
                existing.nombre = p.get("title", existing.nombre)
                existing.precio = float(p.get("price", existing.precio or 0))
                existing.moneda = p.get("currency", existing.moneda or "USD")
                existing.link = affiliate.get("affiliate_link") or p.get("link")
                existing.source = "Hotmart"
                existing.activo = True
            else:
                nuevo = Producto(
                    nombre=p.get("title", "Sin nombre"),
                    descripcion=p.get("description", ""),
                    precio=float(p.get("price", 0)),
                    moneda=p.get("currency", "USD"),
                    link=affiliate.get("affiliate_link") or p.get("link"),
                    source="Hotmart",
                    source_id=p.get("product_id"),
                    activo=True
                )
                db.add(nuevo)
            añadidos += 1
        db.commit()
    finally:
        db.close()

    print(f"[{now}] Investigación completa. Añadidos/actualizados: {añadidos}")
    return {"ok": True, "added": añadidos}

# --- Scheduler que corre periódicamente ---
scheduler = AsyncIOScheduler()
scheduler.add_job(lambda: asyncio.create_task(run_investigation_once()), 'interval', hours=SCHEDULE_CRON_HOURS)
scheduler.start()

# --- Endpoints ---
@app.get("/")
def root():
    return {"status": "ok", "message": "Bot Investigador funcionando 🚀"}

@app.get("/status")
def status():
    return {"status": "ok", "message": "Investigador activo", "hora": datetime.utcnow().isoformat()}

# Endpoint que ejecuta una investigación ahora (protegido si quieres)
@app.post("/investigar_now")
async def investigar_now(x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    res = await run_investigation_once()
    return res

# Admin endpoint para exponer productos (para que el Bot de Ventas los lea vía API si prefieres)
@app.get("/products")
def get_products():
    db = SessionLocal()
    try:
        prods = db.query(Producto).filter(Producto.activo == True).order_by(Producto.created_at.desc()).limit(200).all()
        data = [{
            "id": p.id,
            "nombre": p.nombre,
            "precio": p.precio,
            "moneda": p.moneda,
            "link": p.link,
            "source": p.source,
            "source_id": p.source_id
        } for p in prods]
    finally:
        db.close()
    return {"ok": True, "count": len(data), "products": data}

# Endpoint para que el Bot de ventas mande un update puntual (si lo deseas)
@app.post("/admin/update_products")
async def update_products(request: Request, x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    payload = await request.json()
    # payload es diccionario de productos; lógica simple de inserción/actualización:
    db = SessionLocal()
    updated = []
    try:
        for key, info in payload.items():
            # key puede ser product_id o id
            prod = db.query(Producto).filter(Producto.source_id == key).first()
            if prod:
                prod.nombre = info.get("nombre", prod.nombre)
                prod.precio = float(info.get("precio", prod.precio or 0))
                prod.link = info.get("link", prod.link)
                prod.activo = info.get("activo", prod.activo)
            else:
                new = Producto(
                    nombre=info.get("nombre", "Sin nombre"),
                    descripcion=info.get("descripcion", ""),
                    precio=float(info.get("precio", 0)),
                    moneda=info.get("moneda", "USD"),
                    link=info.get("link"),
                    source=info.get("source", "unknown"),
                    source_id=key,
                    activo=info.get("activo", True)
                )
                db.add(new)
            updated.append(key)
        db.commit()
    finally:
        db.close()
    return {"ok": True, "updated": updated}
