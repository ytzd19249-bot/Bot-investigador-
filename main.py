from fastapi import FastAPI, Request
import requests

app = FastAPI()

# Token válido de su bot
BOT_TOKEN = "8255571596:AAEvqpVQR__FYQUerAVZtEWXNWu1ZtHT3r8"

# Canal donde quiere publicar (asegúrese que el bot sea admin)
CHANNEL_ID = "@infoventas"

# --- Función para enviar mensajes al canal ---
def send_message_to_channel(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": text}
    requests.post(url, data=data)

# --- Función para responder mensajes directos ---
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)

# --- Webhook que recibe mensajes ---
@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/investigar":
            producto = (
                "🔎 Nuevo producto:\n"
                "Nombre: Ejemplo\n"
                "Precio: $25\n"
                "Link: https://amazon.com/ejemplo"
            )
            # Responde al usuario
            send_message(chat_id, "✅ Producto investigado, se mandó al canal Infoventas")
            # Publica en el canal
            send_message_to_channel(producto)

        elif text == "/start":
            send_message(chat_id, "👋 Hola, soy tu bot investigador. Escriba /investigar para probar.")

    return {"ok": True}
