from fastapi import FastAPI, Request
import os
import asyncio
from typing import Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler

app = FastAPI()

# ==========================================================
# VARIABLES DE ENTORNO
# ==========================================================
SALES_PUBLIC_URL = os.getenv("SALES_PUBLIC_URL")
SALES_ADMIN_TOKEN = os.getenv("SALES_ADMIN_TOKEN")

if not SALES_PUBLIC_URL or not SALES_ADMIN_TOKEN:
    print("⚠️ Faltan SALES_PUBLIC_URL o SALES_ADMIN_TOKEN")
else:
    print("✅ Variables de entorno cargadas")

# ==========================================================
# LÓGICA PRINCIPAL
# ==========================================================
async def run_research() -> Dict[str, Any]:
    """
    Ejemplo simple: investiga productos y los envía al bot de ventas.
    """
    print("🔎 Ejecutando investigación...")
    await asyncio.sleep(0.1)
    return {"ok": True, "sent_to": SALES_PUBLIC_URL}

# ==========================================================
# RUTAS
# ==========================================================
@app.get("/")
async def home():
    return {"ok": True, "message": "Bot Investigador en línea ✅"}

@app.post("/debug/run")
async def debug_run(request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    if payload.get("run") is True:
        result = await run_research()
        return {"ok": True, "message": "Investigación completada.", "result": result}
    else:
        result = await run_research()
        return {"ok": True, "message": "Investigación ejecutada (sin flag).", "result": result}

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
    print("⏰ Ejecutando investigación automática cada 12h...")
    await run_research()

@app.on_event("startup")
async def startup_event():
    print("🚀 Bot investigador iniciado correctamente.")
    scheduler.start()
