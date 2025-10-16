from fastapi import FastAPI, Request
import os
import asyncio
from typing import Dict, Any

app = FastAPI()

# ==============================
# VARIABLES DE ENTORNO
# ==============================
SALES_PUBLIC_URL = os.getenv("SALES_PUBLIC_URL")
SALES_ADMIN_TOKEN = os.getenv("SALES_ADMIN_TOKEN")

if not SALES_PUBLIC_URL or not SALES_ADMIN_TOKEN:
    print("⚠️ Faltan SALES_PUBLIC_URL o SALES_ADMIN_TOKEN")
else:
    print("✅ Variables de entorno cargadas")

# ==============================
# LÓGICA BÁSICA (INLINE)
# ==============================
async def run_research() -> Dict[str, Any]:
    """
    Función mínima para probar el flujo.
    Aquí después se conecta la lógica real del investigador.
    """
    print("🔎 Ejecutando investigación (stub)…")
    # Simula trabajo asíncrono
    await asyncio.sleep(0.1)
    # Aquí, cuando tengas la lógica real, mandás data al bot de ventas
    # usando SALES_PUBLIC_URL y SALES_ADMIN_TOKEN.
    return {"ok": True, "sent_to": SALES_PUBLIC_URL}

# ==============================
# RUTAS
# ==============================
@app.get("/")
async def home():
    return {"ok": True, "message": "Bot Investigador en línea ✅"}

@app.post("/debug/run")
async def debug_run(request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    # Opcional: si mandan {"run": true} lo usamos de gatillo
    if payload.get("run") is True:
        result = await run_research()
        return {"ok": True, "message": "Investigación completada.", "result": result}
    else:
        # Igual ejecutamos para pruebas si no viene el flag
        result = await run_research()
        return {"ok": True, "message": "Investigación ejecutada (sin flag).", "result": result}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    _ = await request.json()
    return {"ok": True}

@app.on_event("startup")
async def startup_event():
    print("🚀 Bot investigador iniciado correctamente.")
