import os
import requests
from fastapi import FastAPI, Request

# ===========================
# Cargar variables de entorno
# ===========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_ID = os.getenv("ADMIN_ID")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# ===========================
# Crear app FastAPI
# ===========================
app = FastAPI()


# ===========================
# Endpoint principal (prueba)
# ===========================
@app.get("/")
async def root():
    return {"status": "Bot investigador activo 🚀"}


# ===========================
# Endpoint Webhook de Telegram
# ===========================
@app.post(f"/webhook/{TELEGRAM_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        # Respuesta básica
        if text == "/start":
            send_message(chat_id, "👋 Hola, soy el *Bot Investigador*. Estoy listo para ayudarte 🔎")
        else:
            send_message(chat_id, f"📩 Recibí tu mensaje: {text}")

    return {"ok": True}


# ===========================
# Función para enviar mensajes
# ===========================
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)


# ===========================
# Configuración del webhook
# ===========================
@app.on_event("startup")
def set_webhook():
    if WEBHOOK_URL and TELEGRAM_TOKEN:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
        payload = {"url": f"{WEBHOOK_URL}/webhook/{TELEGRAM_TOKEN}"}
        requests.post(url, json=payload)
