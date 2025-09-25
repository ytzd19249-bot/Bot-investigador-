from fastapi import FastAPI, Request
import requests
import psycopg2
import os

app = FastAPI()

# =========================
# Configuración
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # token del bot
CANAL_ID = "@infoventas2025"        # canal público
DATABASE_URL = os.getenv("DATABASE_URL")  # conexión a PostgreSQL

# =========================
# Conexión a la base de datos
# =========================
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def ensure_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        precio TEXT,
        link TEXT,
        categoria TEXT,
        creador TEXT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def guardar_producto(nombre, descripcion, precio, link_afiliado, categoria, creador):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO productos (nombre, descripcion, precio, link, categoria, creador)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (nombre, descripcion, precio, link_afiliado, categoria, creador)
    )
    conn.commit()
    cur.close()
    conn.close()

# =========================
# Enviar mensaje al canal
# =========================
def send_message_to_channel(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CANAL_ID, "text": text, "parse_mode": "HTML"}
    response = requests.post(url, data=data)
    return response.json()

# =========================
# Webhook
# =========================
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    message = data.get("message", {}).get("text", "")

    if message.startswith("/investigar"):
        # 🔎 Producto ficticio de prueba
        nombre = "Curso de Marketing Digital"
        descripcion = "Aprende a vender en internet desde cero con estrategias probadas."
        precio = "$49"
        link_afiliado = "https://go.hotmart.com/ABC123?ap=XYZ789"
        categoria = "Marketing"
        creador = "Juan Pérez"

        # Guardar en DB
        guardar_producto(nombre, descripcion, precio, link_afiliado, categoria, creador)

        # Notificar al canal
        resultado = (
            f"🔎 <b>Nuevo producto investigado:</b>\n\n"
            f"📌 <b>{nombre}</b>\n"
            f"💡 {descripcion}\n"
            f"💵 {precio}\n"
            f"📂 {categoria}\n"
            f"👨‍💻 Creador: {creador}\n"
            f"🔗 <a href='{link_afiliado}'>Comprar aquí</a>"
        )
        send_message_to_channel(resultado)

    return {"ok": True}

# =========================
# Root
# =========================
@app.get("/")
async def root():
    return {"status": "Bot investigador activo ✅"}

# Crear tabla al iniciar
ensure_table()
