from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- Endpoint principal que recibe los mensajes de Telegram ---
@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_message(chat_id, "Bot Investigador funcionando 🚀")
        else:
            send_message(chat_id, f"Recibí tu mensaje: {text}")

    return {"ok": True}

# --- Función para enviar mensajes ---
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

# --- Configuración del webhook cuando inicia la app ---
@app.on_event("startup")
async def startup_event():
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"
    r = requests.get(url)
    print("Webhook configurado:", r.json())

@app.get("/")
async def home():
    return {"status": "ok", "message": "Bot Investigador funcionando 🚀"}
