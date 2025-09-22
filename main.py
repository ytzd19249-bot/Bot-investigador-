from fastapi import FastAPI, Request
import requests
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler

# --- Configuración ---
app = FastAPI()
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

HOTMART_CLIENT_ID = os.getenv("HOTMART_CLIENT_ID")
HOTMART_CLIENT_SECRET = os.getenv("HOTMART_CLIENT_SECRET")
HOTMART_API_URL = "https://api-sec-vlc.hotmart.com"

# --- Logger ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Endpoint principal que recibe mensajes de Telegram ---
@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_message(chat_id, "🤖 Bot Investigador funcionando 🚀")
        else:
            send_message(chat_id, f"Recibí tu mensaje: {text}")

    return {"ok": True}

# --- Enviar mensajes a Telegram ---
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}")

# --- Configurar webhook al iniciar ---
@app.on_event("startup")
async def startup_event():
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"
    r = requests.get(url)
    logger.info(f"Webhook configurado: {r.json()}")

# --- Endpoint de prueba ---
@app.get("/")
async def home():
    return {"status": "ok", "message": "Bot Investigador funcionando 🚀"}

# --- Función de investigación automática (ejemplo inicial) ---
def investigar_hotmart():
    logger.info("🔎 Buscando productos en Hotmart...")

    # Aquí en futuro: pedir productos reales con HOTMART API
    productos = [
        {"nombre": "Curso de Finanzas", "comision": "40%"},
        {"nombre": "Recetario Saludable", "comision": "30%"},
        {"nombre": "Guía de Inversiones", "comision": "50%"},
    ]

    logger.info(f"Productos investigados: {productos}")
    # Aquí se podría guardar en base de datos

# --- Programar tarea automática cada 2 horas ---
scheduler = BackgroundScheduler()
scheduler.add_job(investigar_hotmart, "interval", hours=2)
scheduler.start()
