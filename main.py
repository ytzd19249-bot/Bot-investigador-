from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# Token del bot (asegurate que lo pongas en las variables de entorno en Render)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

@app.get("/")
async def root():
    return {"status": "Bot Investigador funcionando 🚀"}

# 🔹 Endpoint que Telegram necesita para enviar los mensajes
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    print("📩 Mensaje recibido:", data)

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        # Responder con un eco básico
        reply = f"Recibí tu mensaje: {text}"
        send_message(chat_id, reply)

    return {"ok": True}

def send_message(chat_id, text):
    url = f"{BOT_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)
