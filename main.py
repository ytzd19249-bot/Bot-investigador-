# main.py — BOT INVESTIGADOR
from fastapi import FastAPI, Request
import os
import asyncio
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

app = FastAPI(title="Bot Investigador", version="2.0")

# ==========================================================
# VARIABLES DE ENTORNO
# ==========================================================
SALES_PUBLIC_URL = os.getenv("SALES_PUBLIC_URL", "https://vendedorbt.onrender.com")
SALES_ADMIN_TOKEN = os.getenv("SALES_ADMIN_TOKEN", "ventas_admin_12345")

if not SALES_PUBLIC_URL or not SALES_ADMIN_TOKEN:
    print("⚠️ Faltan SALES_PUBLIC_URL o SALES_ADMIN_TOKEN")
else:
    print(f"✅ Variables cargadas correctamente. Enviando a {SALES_PUBLIC_URL}")

# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================
async def run_research():
    """
    Simula la investigación de productos y los envía al bot de ventas.
    """
    print("🔎 Ejecutando investigación de productos...")

    productos = [
        {
            "titulo": "Reloj deportivo inteligente",
            "precio": 39.99,
            "categoria": "Tecnología",
            "link_afiliado": "https://afiliado.com/reloj",
        },
        {
            "titulo": "Auriculares Bluetooth Pro",
            "precio": 59.90,
            "categoria": "Electrónica",
            "link_afiliado": "https://afiliado.com/auriculares",
        },
        {
            "titulo": "Zapatos deportivos unisex",
            "precio": 74.50,
            "categoria": "Moda",
            "link_afiliado": "https://afiliado.com/zapatos",
        },
    ]

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{SALES_PUBLIC_URL}/ingestion/productos",
                headers={"Authorization": f"Bearer {SALES_ADMIN_TOKEN}"},
                json={"productos": productos},
                timeout=20,
            )
        print(f"📤 Enviados {len(productos)} productos al bot de ventas.")
        print("🧠 Respuesta del bot de ventas:", res.text)
    except Exception as e:
        print(f"❌ Error enviando productos: {e}")

# ==========================================================
# RUTAS
# ==========================================================
@app.get("/")
async def home():
    return {"ok": True, "bot": "investigador", "status": "activo"}

@app.post("/debug/run")
async def debug_run(request: Request):
    """
    Permite ejecutar manualmente la investigación desde el navegador o Postman.
    """
    print("🧠 Ejecución manual solicitada...")
    await run_research()
    return {"ok": True, "mensaje": "Investigación ejecutada manualmente."}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    _ = await request.json()
    return {"ok": True}

# ==========================================================
# CICLO AUTOMÁTICO CADA 12 HORAS
# ==========================================================
scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("interval", hours=12)
async def scheduled_research():
    print("⏰ Investigación automática (cada 12h)...")
    await run_research()

@app.on_event("startup")
async def startup_event():
    print("🚀 Bot investigador iniciado correctamente.")
    scheduler.start()
