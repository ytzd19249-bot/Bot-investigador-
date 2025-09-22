import os
from fastapi import FastAPI, Request
import requests

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Ruta principal para revisar que el bot está vivo
@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot Investigador funcionando 🚀"}

# Ruta para recibir mensajes desde Telegram
@app.post(f"/webhook/{TELEGRAM_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        reply = f"👋 Hola, soy el InvestigadorDigitalBot.\n\nMe escribiste: {text}"

        # Responder al usuario
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": reply
        })

    return {"status": "ok"}

# Configurar webhook automáticamente al iniciar
@app.on_event("startup")
async def set_webhook():
    if TELEGRAM_TOKEN and WEBHOOK_URL:
        full_webhook_url = f"{WEBHOOK_URL}/webhook/{TELEGRAM_TOKEN}"
        requests.get(f"{TELEGRAM_API_URL}/setWebhook?url={full_webhook_url}")
