from fastapi import FastAPI, Request
import requests
import os
from db import SessionLocal, Producto

app = FastAPI()

# Tokens y configs desde Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

# ==========================
# Función para enviar mensaje
# ==========================
async def enviar_mensaje(chat_id: int, texto: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto}
    requests.post(url, json=payload)

# ==========================
# Webhook principal
# ==========================
@app.post("/webhook")
async def webhook(request: Request):
    update = await request.json()
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not text:
        return {"ok": True}

    # Comando /start
    if text.startswith("/start"):
        await enviar_mensaje(chat_id, "👋 ¡Bienvenido al Bot Investigador!")
        return {"ok": True}

    # Comando /ver_productos
    if text.startswith("/ver_productos"):
        return await ver_productos(update)

    return {"ok": True}

# ==========================
# Endpoint para /ver_productos
# ==========================
@app.post("/ver_productos")
async def ver_productos(update: dict):
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")

    db = SessionLocal()
    try:
        productos = db.query(Producto).limit(10).all()  # primeros 10
        if not productos:
            respuesta = "📂 No hay productos guardados todavía."
        else:
            respuesta = "📦 Productos en la base de datos:\n\n"
            for p in productos:
                respuesta += f"➡️ {p.nombre} | {p.precio} {p.moneda}\n"
    except Exception as e:
        respuesta = f"⚠️ Error al consultar DB: {e}"
    finally:
        db.close()

    await enviar_mensaje(chat_id, respuesta)
    return {"ok": True}
