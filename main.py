# main.py — Bot Investigador Limpio (sin base de datos)
import os
import asyncio
from typing import List, Dict
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# ======================
# VARIABLES DE ENTORNO
# ======================
SALES_PUBLIC_URL = os.getenv("SALES_PUBLIC_URL", "").rstrip("/")
SALES_ADMIN_TOKEN = os.getenv("SALES_ADMIN_TOKEN", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CANAL_ID = os.getenv("CANAL_ID", "")

# ======================
# APP Y SCHEDULER
# ======================
scheduler = AsyncIOScheduler()
app = FastAPI(title="Bot Investigador Autónomo")

# ======================
# ENVIAR MENSAJE AL CANAL (opcional)
# ======================
async def send_to_channel(text: str):
    if not (BOT_TOKEN and CANAL_ID):
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CANAL_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            await client.post(url, data=payload)
        except Exception:
            pass

# ======================
# INVESTIGACIÓN FICTICIA
# ======================
async def investigar_fuentes() -> List[Dict]:
    # Aquí luego pondremos la lógica real
    await asyncio.sleep(0.2)
    return [
        {
            "nombre": "Curso de Marketing Digital",
            "descripcion": "Aprende a vender en internet con estrategias probadas.",
            "precio": 49.0,
            "moneda": "USD",
            "link": "https://go.hotmart.com/ABC123?ap=XYZ789",
            "source": "investigador",
            "activo": True,
        },
        {
            "nombre": "Ebook: Recetas en Freidora de Aire",
            "descripcion": "50 recetas prácticas para todos los días.",
            "precio": 12.0,
            "moneda": "USD",
            "link": "https://gum.co/recetas-freidora",
            "source": "investigador",
            "activo": True,
        },
    ]

# ======================
# SINCRONIZAR CON BOT DE VENTAS
# ======================
async def sync_con_ventas(items: List[Dict]) -> Dict:
    if not SALES_PUBLIC_URL or not SALES_ADMIN_TOKEN:
        return {"ok": False, "error": "Faltan SALES_PUBLIC_URL o SALES_ADMIN_TOKEN"}
    url = f"{SALES_PUBLIC_URL}/admin/sync_products"
    headers = {"x-admin-token": SALES_ADMIN_TOKEN}
    payload = {"items": items}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, json=payload, headers=headers)
        try:
            return r.json()
        except Exception:
            return {"ok": False, "status_code": r.status_code, "text": r.text}

# ======================
# CICLO PRINCIPAL
# ======================
async def run_job():
    productos = await investigar_fuentes()
    resp = await sync_con_ventas(productos)
    try:
        await send_to_channel(f"🔎 <b>Investigación ejecutada</b>\nSe enviaron <b>{len(productos)}</b> producto(s) al catálogo.")
    except Exception:
        pass
    return resp

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(run_job, CronTrigger(hour="0,12", minute=0))  # Cada 12 horas
    scheduler.start()
    asyncio.create_task(run_job())  # Ejecuta una vez al iniciar
    yield
    scheduler.shutdown()

app = FastAPI(title="Bot Investigador Autónomo", lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Investigador activo (00:00/12:00 UTC)."}

@app.post("/debug/run")
async def debug_run():
    return await run_job()
