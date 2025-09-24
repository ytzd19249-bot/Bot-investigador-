import os
import re
import httpx
import openai
from fastapi import FastAPI, Request, HTTPException
from db import SessionLocal, Producto, init_db
from sqlalchemy.orm import Session
from telegram import Bot

app = FastAPI(title="Bot Investigador")

# init DB (crea tablas si no existen)
init_db()

# ENV (poner en Render)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")          # token del bot de Telegram
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")        # clave OpenAI (opcional)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")          # token que usa el bot investigador para actualizar catálogo
PUBLIC_URL = os.getenv("PUBLIC_URL", "")            # ej: https://bot-investigador.onrender.com
REPORT_CHAT_ID = os.getenv("REPORT_CHAT_ID", "")    # ID de chat donde se manda reporte

BASE_TELEGRAM = f"https://api.telegram.org/bot{BOT_TOKEN}"

# configurar OpenAI si existe
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Bot de Telegram para reportes
tg_bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None

def send_report(text: str):
    """Manda resumen al admin por Telegram"""
    if tg_bot and REPORT_CHAT_ID:
        try:
            tg_bot.send_message(chat_id=REPORT_CHAT_ID, text=text, parse_mode="Markdown")
        except Exception as e:
            print("Error enviando reporte:", e)

# enviar mensaje genérico a Telegram
async def send_message(chat_id: int, text: str, parse_mode: str = "Markdown"):
    if not BOT_TOKEN:
        return None
    url = f"{BASE_TELEGRAM}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            r = await client.post(url, json=payload)
            return r.json()
        except Exception:
            return None

# normalizar texto
def normalize_text(t: str) -> str:
    return re.sub(r"\s+", " ", t.strip().lower())

# lógica (si en algún momento se quiere testear en Telegram)
async def handle_user_message(chat_id: int, text: str, db: Session):
    t = normalize_text(text)

    # saludos
    if re.search(r"\b(hola|buenas|buenos días|buenas tardes|buenas noches|hey)\b", t):
        return await send_message(chat_id, "👋 Soy el Bot Investigador. Yo no vendo, solo investigo productos.")

    # catálogo rápido
    if t == "productos":
        productos = db.query(Producto).filter(Producto.activo == True).limit(20).all()
        if not productos:
            return await send_message(chat_id, "📭 No hay productos registrados todavía.")
        lines = [f"{p.id}. {p.nombre} — {p.precio} {p.moneda}" for p in productos]
        return await send_message(chat_id, "📊 Productos investigados:\n\n" + "\n".join(lines))

    return await send_message(chat_id, "🤖 Soy el bot investigador, trabajo en segundo plano buscando productos Hotmart.")

# webhook Telegram (opcional, si quiere hablar con el bot)
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

    db = SessionLocal()
    try:
        await handle_user_message(chat_id, text, db)
    finally:
        db.close()

    return {"ok": True}

# Endpoint admin para actualizar catálogo
@app.post("/admin/update_products")
async def admin_update_products(request: Request):
    token = request.headers.get("x-admin-token", "")
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    data = await request.json()
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Invalid body")

    db = SessionLocal()
    updated = []
    try:
        for k, v in data.items():
            pid = int(k) if str(k).isdigit() else None
            if pid:
                prod = db.query(Producto).filter(Producto.id == pid).first()
            else:
                prod = None

            if prod:
                prod.nombre = v.get("nombre", prod.nombre)
                prod.descripcion = v.get("descripcion", prod.descripcion)
                prod.precio = float(v.get("precio", prod.precio or 0))
                prod.moneda = v.get("moneda", prod.moneda or "USD")
                prod.link = v.get("link", prod.link)
                prod.source = v.get("source", prod.source)
                prod.activo = v.get("activo", prod.activo)
            else:
                new = Producto(
                    nombre=v.get("nombre", "Sin nombre"),
                    descripcion=v.get("descripcion", ""),
                    precio=float(v.get("precio", 0)),
                    moneda=v.get("moneda", "USD"),
                    link=v.get("link"),
                    source=v.get("source"),
                    activo=v.get("activo", True),
                )
                db.add(new)
            updated.append(k)
        db.commit()
    finally:
        db.close()

    # reporte al admin
    send_report(f"✅ Investigación completada.\nProductos actualizados: {len(updated)}")
    return {"ok": True, "updated": updated}

# Endpoint admin para listar productos
@app.get("/admin/list_products")
async def list_products(request: Request):
    token = request.headers.get("x-admin-token", "")
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    db = SessionLocal()
    try:
        productos = db.query(Producto).all()
        return [
            {
                "id": p.id,
                "nombre": p.nombre,
                "precio": p.precio,
                "moneda": p.moneda,
                "activo": p.activo,
                "link": p.link,
                "source": p.source
            }
            for p in productos
        ]
    finally:
        db.close()

@app.get("/")
def root():
    return {"status": "ok", "message": "Bot Investigador funcionando 🚀"}
