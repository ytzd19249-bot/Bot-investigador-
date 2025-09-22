from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import sqlite3

app = FastAPI()

# Middleware para CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# CONFIG TELEGRAM
# ---------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ---------------------------
# BASE DE DATOS SQLITE
# ---------------------------
DB_NAME = "mensajes.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            usuario TEXT,
            mensaje TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def guardar_mensaje(chat_id, usuario, mensaje):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mensajes (chat_id, usuario, mensaje) VALUES (?, ?, ?)",
                   (chat_id, usuario, mensaje))
    conn.commit()
    conn.close()

def obtener_mensajes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, chat_id, usuario, mensaje FROM mensajes ORDER BY id DESC")
    datos = cursor.fetchall()
    conn.close()
    return datos

def enviar_mensaje(chat_id, texto):
    requests.post(f"{BASE_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": texto
    })

# ---------------------------
# ENDPOINTS
# ---------------------------
@app.get("/")
def home():
    return {"status": "Bot Investigador funcionando 🚀"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        usuario = data["message"]["from"].get("username", "desconocido")
        texto = data["message"].get("text", "")

        # Guardar en BD
        guardar_mensaje(chat_id, usuario, texto)

        # Responder
        if texto == "/start":
            reply = "🤖 Hola mae, soy el Bot Investigador. Estoy activo 🚀"
        elif texto == "/status":
            reply = "✅ Todo está funcionando bien"
        else:
            reply = f"Recibí tu mensaje: {texto}"

        enviar_mensaje(chat_id, reply)

    return {"ok": True}

@app.get("/mensajes")
def ver_mensajes():
    datos = obtener_mensajes()
    return {"mensajes": [
        {"id": d[0], "chat_id": d[1], "usuario": d[2], "mensaje": d[3]}
        for d in datos
    ]}
