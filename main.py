import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

@app.post(f"/webhook/{BOT_TOKEN}")
async def webhook(request: Request):
    data = await request.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            reply = "🤖 Bot Investigador funcionando 🚀"
        elif text == "/status":
            reply = "✅ Estado: Activo y escuchando 👂"
        else:
            reply = f"Recibí tu mensaje: {text}"

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json={"chat_id": chat_id, "text": reply}
            )

    return JSONResponse(content={"status": "ok"})

@app.get("/")
async def root():
    return {"status": "Bot Investigador funcionando 🚀"}
