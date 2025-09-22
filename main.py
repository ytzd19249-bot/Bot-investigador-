from fastapi import FastAPI, Request
import requests, os, logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from hotmart_api import obtener_productos, filtrar_productos

app = FastAPI()
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- Enviar mensajes a Telegram
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

# --- Webhook de Telegram
@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_message(chat_id, "🤖 Bot Investigador funcionando 🚀")
        elif text == "/productos":
            productos = obtener_productos()
            top = filtrar_productos(productos)[:5]
            respuesta = "\n\n".join(
                [f"🔥 {p['name']}\n💲 Comisión: {p['commission']['value']}" for p in top]
            )
            send_message(chat_id, respuesta or "No encontré productos ahora mismo")
        else:
            send_message(chat_id, f"Recibí tu mensaje: {text}")
    return {"ok": True}

# --- Tarea automática: investiga cada hora
def investigar_hotmart():
    productos = obtener_productos()
    buenos = filtrar_productos(productos)
    logging.info(f"Productos investigados: {len(buenos)}")

scheduler = AsyncIOScheduler()
scheduler.add_job(investigar_hotmart, "interval", hours=1)
scheduler.start()

@app.on_event("startup")
async def startup_event():
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"
    r = requests.get(url)
    logging.info(f"Webhook configurado: {r.json()}")

@app.get("/")
async def home():
    return {"status": "ok", "message": "Bot Investigador funcionando 🚀"}
