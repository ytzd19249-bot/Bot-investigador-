import os
from fastapi import FastAPI, Request
import requests

app = FastAPI()

# Variables de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_ID = os.getenv("ADMIN_ID")  # tu ID de usuario en Telegram

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


@app.on_event("startup")
async def set_webhook():
    """
    Configura el webhook de Telegram al iniciar el servidor en Render
    """
    url = f"{BASE_URL}/setWebhook"
    data = {"url": f"{WEBHOOK_URL}/webhook/{TELEGRAM_TOKEN}"}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("✅ Webhook configurado correctamente")
    else:
        print("⚠️ Error al configurar webhook:", response.text)


@app.post(f"/webhook/{TELEGRAM_TOKEN}")
async def telegram_webhook(request: Request):
    """
    Recibe mensajes de Telegram y responde
    """
    data = await request.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        # Respuesta básica
        if text.lower() == "/start":
            send_message(chat_id, "👋 Hola, soy el *Bot Investigador*. Estoy en línea 🚀")
        else:
            send_message(chat_id, f"Recibí tu mensaje: {text}")

    return {"ok": True}


@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot Investigador funcionando 🚀"}


def send_message(chat_id, text):
    """
    Envía un mensaje de texto al chat indicado
    """
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, data=payload)
