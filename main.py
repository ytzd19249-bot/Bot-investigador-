import os
import re
import httpx
import openai
from fastapi import FastAPI, Request, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from db import SessionLocal, Producto, init_db
from sqlalchemy.orm import Session
from datetime import datetime

app = FastAPI(title="Bot Investigador - CompraFácil")

# init DB
init_db()

# ENV VARS
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
PUBLIC_URL = os.getenv("PUBLIC_URL", "")
BASE_TELEGRAM = f"https://api.telegram.org/bot{BOT_TOKEN}"

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


# enviar mensaje a telegram
async def send_message(chat_id: int, text: str):
    if not BOT_TOKEN:
        return None
    url = f"{BASE_TELEGRAM}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            r = await client.post(url, json=payload)
            return r.json()
        except Exception:
            return None


# ===== FUNCIONES DE INVESTIGACIÓN =====
def investigar_y_afiliar():
    """Simulación: Investiga productos en Hotmart y los guarda en DB ya afiliados."""
    db = SessionLocal()
    try:
        # aquí en real se conectaría con la API de Hotmart (placeholder por ahora)
        productos_fake = [
            {
                "nombre": "Curso Python Pro",
                "descripcion": "Aprende Python de 0 a avanzado",
                "precio": 49.99,
                "moneda": "USD",
                "link": "https://hotmart.com/afiliado/python-pro",
            },
            {
                "nombre": "Marketing Digital Master",
                "descripcion": "Estrategias para crecer ventas online",
                "precio": 79.99,
                "moneda": "USD",
                "link": "https://hotmart.com/afiliado/mkt-master",
            },
        ]

        for p in productos_fake:
            existe = (
                db.query(Producto)
                .filter(Producto.nombre == p["nombre"])
                .first()
            )
            if not existe:
                nuevo = Producto(
                    nombre=p["nombre"],
                    descripcion=p["descripcion"],
                    precio=p["precio"],
                    moneda=p["moneda"],
                    link=p["link"],
                    source="hotmart",
                    activo=True,
                    created_at=datetime.utcnow(),
                )
                db.add(nuevo)
                print(f"✅ Insertado {p['nombre']} en DB")

        db.commit()
    except Exception as e:
        print("❌ Error investigando:", e)
    finally:
        db.close()


# ===== CRONJOB (2 veces al día) =====
scheduler = BackgroundScheduler()
scheduler.add_job(investigar_y_afiliar, "interval", hours=12)
scheduler.start()


# ===== ENDPOINTS =====
@app.get("/")
def root():
    return {"ok": True, "msg": "Bot Investigador activo 🚀"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid json")

    if "message" not in update:
        return {"ok": True}

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")

    # solo admin puede consultar catálogo del investigador
    if text.strip() == ADMIN_TOKEN:
        db = SessionLocal()
        try:
            productos = (
                db.query(Producto)
                .filter(Producto.activo == True)
                .order_by(Producto.created_at.desc())
                .limit(10)
                .all()
            )
            if not productos:
                await send_message(chat_id, "📭 No hay productos en la base de datos aún.")
            else:
                lines = [f"{p.id}. {p.nombre} — {p.precio} {p.moneda}" for p in productos]
                await send_message(chat_id, "🛍️ Últimos productos investigados:\n\n" + "\n".join(lines))
        finally:
            db.close()

    return {"ok": True}
