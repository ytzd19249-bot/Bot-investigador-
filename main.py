import os
import logging
from fastapi import FastAPI, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from hotmart_api import obtener_productos, filtrar_productos, afiliar_producto
from db import init_db, guardar_producto

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI()

# Inicializar DB
init_db()

# Scheduler
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(investigar_hotmart, "interval", hours=12)
    scheduler.start()
    logger.info("Bot iniciado y scheduler corriendo cada 12 horas 🚀")

async def investigar_hotmart():
    logger.info("🔎 Investigando productos Hotmart...")
    productos = await obtener_productos()
    seleccionados = filtrar_productos(productos)
    for p in seleccionados:
        try:
            enlace = await afiliar_producto(p["id"])
            p["affiliate_link"] = enlace
            guardar_producto(p)
            logger.info(f"✅ Guardado {p['name']} con enlace {enlace}")
        except Exception as e:
            logger.error(f"Error afiliando {p['name']}: {e}")

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    logger.info(f"📩 Webhook recibido: {data}")
    return {"ok": True}
