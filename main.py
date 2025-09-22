import os
import logging
import requests
from fastapi import FastAPI, Request
from apscheduler.schedulers.background import BackgroundScheduler

from hotmart_api import obtener_productos, filtrar_productos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables de entorno
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = FastAPI()
scheduler = BackgroundScheduler()

# --- Función para mandar mensajes a Telegram ---
def enviar_mensaje(mensaje: str):
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("⚠️ No hay BOT_TOKEN o CHAT_ID configurados")
        return
    try:
        url = f"{BASE_URL}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, data=data)
        logger.info("📩 Mensaje enviado a Telegram")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a Telegram: {e}")

# --- Función principal de investigación ---
def investigar_hotmart():
    logger.info("🔎 Investigando productos en Hotmart...")

    productos = obtener_productos()
    filtrados = filtrar_productos(productos)

    if not filtrados:
        enviar_mensaje("⚠️ No se encontraron productos rentables en este momento.")
    else:
        for prod in filtrados:
            mensaje = (
                f"✅ *{prod['nombre']}*\n"
                f"📊 Ventas: {prod['ventas']}\n"
                f"💵 Comisión: ${prod['comision']}"
            )
            enviar_mensaje(mensaje)

# --- Webhook de Telegram (evita 404) ---
@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    return {"ok": True}

# --- Arranque automático ---
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Iniciando bot investigador...")
    scheduler.add_job(investigar_hotmart, "interval", hours=6)  # cada 6 horas
    scheduler.start()
    investigar_hotmart()  # ejecuta apenas arranca
