from fastapi import FastAPI, Request
import requests

app = FastAPI()

# Token de su bot
BOT_TOKEN = "8278402782:AAGNfynGvMRkC2f09rv6-yonq6_jFm1GRlM"

# Canal donde quiere publicar (asegúrese que el bot sea admin)
CHANNEL_ID = "@infoventas"

# --- Función para enviar mensajes al canal ---
def send_message_to_channel(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": text}
    requests.post(url, data=data)

# --- Webhook que recibe mensajes ---
@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    # Ver quién envió el mensaje y cuál fue el texto
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        # Si alguien escribe /investigar se simula un producto
        if text == "/investigar":
            producto = "🔎 Nuevo producto:\nNombre: Ejemplo\nPrecio: $25\nLink: https://amazon.com/ejemplo"
            # Responde al usuario
            send_message(chat_id, "✅ Producto investigado, se mandó al canal Infoventas")
            # Manda al canal automáticamente
            send_message_to_channel(producto)

        elif text == "/start":
            send_message(chat_id, "👋 Hola, soy tu bot investigador. Escriba /investigar para probar.")
    
    return {"ok": True}

# --- Función para enviar mensajes directos a usuarios ---
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)
