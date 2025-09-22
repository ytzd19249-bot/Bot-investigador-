from fastapi import FastAPI, Request
import httpx
import os

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot Investigador funcionando 🚀"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()

        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")

            if text.lower() == "/start":
                reply = "Hola 👋, soy el *Bot Investigador*. Estoy listo para buscar nichos y productos 🔎"
            else:
                reply = f"Recibí tu mensaje: {text}"

            # responder al usuario
            async with httpx.AsyncClient() as client:
                await client.post(f"{BASE_URL}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": reply,
                    "parse_mode": "Markdown"
                })

        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
