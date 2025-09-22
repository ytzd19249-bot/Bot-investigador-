# main.py
import os
import asyncio
import logging
import requests
from fastapi import FastAPI, Request, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from hotmart_api import obtener_productos, filtrar_productos, afiliar_producto
from db import init_db, guardar_producto
from models import Producto

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Env
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # ej: https://tu-app.onrender.com
CHECK_HOURS = float(os.getenv("CHECK_HOURS", "12"))  # default 12 horas
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # opcional para notificar

app = FastAPI()

# Init DB tables
@app.on_event("startup")
async def startup():
    logger.info("Iniciando servicio y DB...")
    init_db()
    # configurar webhook en Telegram (apunta al endpoint /webhook/{TOKEN})
    if TOKEN and WEBHOOK_URL:
        try:
            set_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}/webhook/{TOKEN}"
            r = requests.get(set_url, timeout=10)
            logger.info("Webhook set response: %s", r.json())
        except Exception as e:
            logger.warning("No se pudo setear webhook: %s", e)

    # iniciar scheduler
    scheduler.start()
    logger.info("Scheduler iniciado. Primera ejecución en arranque.")
    # lanzar primero una ejecución al arrancar
    asyncio.create_task(run_investigation_once())

# scheduler
scheduler = AsyncIOScheduler()

async def investigar_hotmart():
    logger.info("🔎 Ejecutando investigación Hotmart (automático)...")
    try:
        productos_raw = await obtener_productos()
        seleccionados = filtrar_productos(productos_raw, min_comision=1.0)
        logger.info("Seleccionados: %d", len(seleccionados))

        for p in seleccionados:
            prod_obj = {
                "id": p.get("id"),
                "nombre": p.get("nombre"),
                "comision": p.get("comision"),
                "ventas": p.get("ventas"),
                "precio": p.get("precio", None),
                "moneda": p.get("moneda", None),
                "link": p.get("link")
            }
            # intentar afiliar (no bloqueante)
            try:
                res = await afiliar_producto(prod_obj["id"])
                if isinstance(res, dict) and res.get("ok") is False:
                    logger.warning("Afiliación no OK: %s", res.get("detail"))
                else:
                    logger.info("Afiliación solicitada OK para %s", prod_obj["id"])
            except Exception as e:
                logger.warning("Error al afiliar %s: %s", prod_obj["id"], e)

            # guardar en DB (sync)
            try:
                guardar_producto(prod_obj)
                logger.info("Guardado en DB: %s", prod_obj["nombre"])
            except Exception as e:
                logger.error("Error guardando en DB %s: %s", prod_obj["id"], e)

        # opcional: notificar por Telegram
        if TELEGRAM_CHAT_ID:
            try:
                mensaje = f"Investigación completada: {len(seleccionados)} productos seleccionados."
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje})
            except Exception:
                pass

    except Exception as e:
        logger.exception("Error en investigar_hotmart: %s", e)

# wrapper para scheduler que acepta coroutine
async def run_investigation_once():
    await investigar_hotmart()

# Schedule job (cada CHECK_HOURS horas)
scheduler.add_job(lambda: asyncio.create_task(investigar_hotmart()), "interval", hours=CHECK_HOURS)

# --- Endpoints ---
@app.get("/")
def home():
    return {"status": "ok", "message": "Bot Investigador funcionando 🚀"}

@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    # recibe updates de Telegram si quiere usarse manualmente
    if token != TOKEN:
        raise HTTPException(status_code=403, detail="token inválido")
    data = await request.json()
    logger.info("Webhook update: %s", data)
    # opcional: si quiere forzar investigación con comando
    try:
        if "message" in data:
            text = data["message"].get("text", "")
            chat_id = data["message"]["chat"]["id"]
            if text and text.strip().lower() in ("/investigar","/run"):
                # lanzar investigación asíncrona
                asyncio.create_task(investigar_hotmart())
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "Voy a investigar ahora mismo."})
    except Exception:
        pass
    return {"ok": True}

@app.get("/productos")
def listar_productos():
    # devuelve productos guardados (limitado)
    from db import SessionLocal
    s = SessionLocal()
    rows = s.query(Producto).order_by(Producto.creado_en.desc()).limit(200).all()
    s.close()
    result = []
    for r in rows:
        result.append({
            "producto_id": r.producto_id,
            "nombre": r.nombre,
            "precio": r.precio,
            "comision": r.comision,
            "ventas": r.ventas,
            "link_afiliado": r.link_afiliado,
            "creado_en": r.creado_en.isoformat()
        })
    return result
