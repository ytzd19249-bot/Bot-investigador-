from fastapi import FastAPI, Request
import requests
import sqlite3

app = FastAPI()

# Token del bot
BOT_TOKEN = "8255571596:AAEvqpVQR__FYQUerAVZtEWXNWu1ZtHT3r8"

# Canal donde quiere publicar
CHANNEL_ID = "@infoventas"

# --- Base de datos ---
def init_db():
    conn = sqlite3.connect("productos.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            precio TEXT,
            link TEXT
        )
    """)
    conn.commit()
    conn.close()

def guardar_producto(nombre, precio, link):
    conn = sqlite3.connect("productos.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO productos (nombre, precio, link) VALUES (?, ?, ?)", (nombre, precio, link))
    conn.commit()
    conn.close()

# --- Enviar mensaje a canal ---
def send_message_to_channel(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": text}
    requests.post(url, data=data)

# --- Enviar mensaje directo ---
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)

# --- Webhook ---
@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/investigar":
            nombre = "Ejemplo"
            precio = "$25"
            link = "https://amazon.com/ejemplo"

            producto = f"🔎 Nuevo producto:\nNombre: {nombre}\nPrecio: {precio}\nLink: {link}"

            # Guardar en DB
            guardar_producto(nombre, precio, link)

            # Responder al usuario
            send_message(chat_id, "✅ Producto investigado y guardado, se mandó al canal Infoventas")

            # Mandar al canal
            send_message_to_channel(producto)

        elif text == "/productos":
            # Recuperar productos de la DB
            conn = sqlite3.connect("productos.db")
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, precio, link FROM productos ORDER BY id DESC LIMIT 5")
            rows = cursor.fetchall()
            conn.close()

            if rows:
                lista = "📦 Últimos productos:\n\n"
                for r in rows:
                    lista += f"- {r[0]} ({r[1]})\n{r[2]}\n\n"
            else:
                lista = "❌ No hay productos guardados."

            send_message(chat_id, lista)

        elif text == "/start":
            send_message(chat_id, "👋 Hola, soy tu bot investigador.\n\nComandos disponibles:\n/investigar → Simular investigación\n/productos → Ver últimos guardados")

    return {"ok": True}

# Inicializar DB al arrancar
init_db()
