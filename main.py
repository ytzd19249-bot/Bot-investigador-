from fastapi import FastAPI, Request
import os
import asyncio
from dotenv import load_dotenv
from core.researcher import run_research

load_dotenv()

app = FastAPI()

# ==========================================================
# VARIABLES DE ENTORNO
# ==========================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
SALES_PUBLIC_URL = os.getenv("SALES_PUBLIC_URL")
SALES_ADMIN_TOKEN = os.getenv("SALES_ADMIN_TOKEN")

# ==========================================================
# VERIFICAR VARIABLES NECESARIAS
# ==========================================================
if not SALES_PUBLIC_URL or not SALES_ADMIN_TOKEN:
    print("⚠️ ERROR: Faltan SALES_PUBLIC_URL o SALES_ADMIN_TOKEN")
else:
    print("✅ Variables de entorno cargadas correctamente")

# ==========================================================
# RUTA PRINCIPAL
# ==========================================================
@app.get("/")
async def home():
    return {"ok": True, "message": "Bot Investigador en línea ✅"}

# ==========================================================
# RUTA DE DEPURACIÓN MANUAL (para Hoppscotch)
# ==========================================================
@app.post("/debug/run")
async def debug_run(request: Request):
    try:
        await run_research()
        return {"ok": True, "message": "Investigación completada y enviada al bot de ventas."}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ==========================================================
# WEBHOOK DE TELEGRAM (si el bot lo usa)
# ==========================================================
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    # Aquí podrías procesar mensajes si querés que responda directamente
    return {"ok": True}

# ==========================================================
# ARRANQUE AUTOMÁTICO (por si se usa programador interno)
# ==========================================================
@app.on_event("startup")
async def startup_event():
    print("🚀 Bot investigador iniciado correctamente.")
    # Si querés que corra al iniciar, descomentá esta línea:
    # await run_research()
