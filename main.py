from fastapi import FastAPI, Request
import os
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from hotmart_api import obtener_productos, filtrar_productos, afiliar_producto
from db import init_db, guardar_producto

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")  # tu chat_id en Telegram

app = FastAPI()

init_db()
scheduler = AsyncIOScheduler()

async def enviar_telegram(mensaje: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": ADMIN_ID, "text": mensaje})

async def investigar_hotmart():
    productos = await obtener_productos()
    filtrados = filtrar_productos(productos)

    reporte = f"📊 Reporte Hotmart\nProductos encontrados: {len(productos)}\nFiltrados: {len(filtrados)}\n"
    for p in filtrados[:5]:  # muestra solo 5
        nombre = p.get("name", "Sin nombre")
        precio = p.get("price", 0)
        comision = p.get("commission", 0)
        link = p.get("sales_page", "#")
        guardar_producto(nombre, precio, comision, link)
        reporte += f"\n✅ {nombre} | 💵 {precio} | 💸 {comision}%"

    await enviar_telegram(reporte)

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(investigar_hotmart, "interval", hours=12)  # 2 veces al día
    scheduler.start()
    await enviar_telegram("🤖 Bot Investigador iniciado y listo 🚀")

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if chat_id == int(ADMIN_ID):
        if text.lower() == "/status":
            await enviar_telegram("✅ Bot funcionando y vigilando Hotmart")
        elif text.lower() == "/investigar":
            await investigar_hotmart()
            await enviar_telegram("🔍 Investigación ejecutada manualmente")
    return {"ok": True}

@app.get("/")
def home():
    return {"status": "Bot Investigador funcionando 🚀"}
