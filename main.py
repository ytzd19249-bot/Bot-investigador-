# main.py  — Bot Investigador
import os
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx

app = FastAPI()

# ==========================================================
# VARIABLES DE ENTORNO
# ==========================================================
SALES_PUBLIC_URL = os.getenv("SALES_PUBLIC_URL")  # Ej: https://vendedorbt.onrender.com
SALES_ADMIN_TOKEN = os.getenv("SALES_ADMIN_TOKEN", "ventas_admin_12345")

if not SALES_PUBLIC_URL or not SALES_ADMIN_TOKEN:
    print("⚠️ Faltan SALES_PUBLIC_URL o SALES_ADMIN_TOKEN")
else:
    print(f"✅ Variables cargadas correctamente. Enviando a {SALES_PUBLIC_URL}")

# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================
async def run_research() -> Dict[str, Any]:
    """
    Investiga productos y los envía al bot de ventas.
    """
    print("🔎 Ejecutando investigación...")

    # Ejemplo de productos encontrados
    productos = [
        {
            "titulo": "Reloj Deportivo Inteligente",
            "precio": 39.99,
            "categoria": "Electrónica",
            "link_afiliado": "https://hotmart.com/reloj"
        },
        {
            "titulo": "Audífonos Bluetooth",
            "precio": 25.50,
            "categoria": "Audio",
            "link_afiliado": "https://hotmart.com/audifonos"
        },
        {
            "titulo": "Zapatillas Deportivas",
            "precio": 49.90,
            "categoria": "Moda",
            "link_afiliado": "https://hotmart.com/zapatillas"
        }
    ]

    # Enviar productos al bot de ventas
    async with httpx.AsyncClient() as client:
        url = f"{SALES_PUBLIC_URL}/ingestion/productos"
        headers = {"Authorization": f"Bearer {SALES_ADMIN_TOKEN}"}
        payload = {"productos": productos}

        try:
            res = await client.post(url, json=payload, headers=headers, timeout=30)
            print("📦 Respuesta del bot de ventas:", res.json())
        except Exception as e:
            print("❌ Error enviando productos:", e)

    return {"ok": True, "sent_to": SALES_PUBLIC_URL, "productos_enviados": len(productos)}

# ==========================================================
# RUTAS FASTAPI
# ==========================================================
@app.get("/")
async def home():
    return {"ok": True, "message": "Bot Investigador en línea ✅"}

@app.post("/debug/run")
async def debug_run(request: Request):
    """
    Permite ejecutar la investigación manualmente desde Render o Postman.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    print("🧠 Ejecución manual solicitada:", payload)
    result = await run_research()
    return {"ok": True, "message": "Investigación ejecutada correctamente", "result": result}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Solo para compatibilidad con Telegram.
    """
    _ = await request.json()
    return {"ok": True}

# ==========================================================
# CICLO AUTOMÁTICO CADA 12 HORAS
# ==========================================================
scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("interval", hours=12)
async def scheduled_research():
    print("⏰ Ejecutando investigación automática cada 12h...")
    await run_research()

@app.on_event("startup")
async def startup_event():
    print("🚀 Bot investigador iniciado correctamente.")
    scheduler.start()
