import os
import requests
from fastapi import FastAPI, Request

# =========================================================
# Inicialización de la app
# =========================================================
app = FastAPI()

# =========================================================
# Variables de entorno
# =========================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_ID = os.getenv("ADMIN_ID")   # por si quieres validar admin en el futuro

# =========================================================
# Endpoint raíz (para probar que el servidor está vivo)
# =========================================================
@app.get("/")
def home():
    return {"status": "ok", "message": "Servidor InvestigadorDigitalBot en línea 🚀"}

# =========================================================
# Endpoint Webhook de Telegram
# =========================================================
@app.post(f"/webhook/{TELEGRAM_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        # Respuesta básica
        if text == "/start":
            send_message(chat_id, "👋 Hola, soy tu InvestigadorDigitalBot. 🚀")
        else:
            send_message(chat_id, f"Recibí tu mensaje: {text}")

    return {"ok": True}

# =========================================================
# Función para enviar mensajes
# =========================================================
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

# =========================================================
# Configuración del webhook al iniciar
# =========================================================
@app.on_event("startup")
def set_webhook():
    if WEBHOOK_URL and TELEGRAM_TOKEN:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
        payload = {"url": f"{WEBHOOK_URL}/webhook/{TELEGRAM_TOKEN}"}
        requests.post(url, json=payload)

# =========================================================
# Punto de entrada para Render / Local
# =========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=False)
