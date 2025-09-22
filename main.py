from fastapi import FastAPI
import requests
import os
from dotenv import load_dotenv
import pandas as pd
from bs4 import BeautifulSoup

# Cargar variables de entorno
load_dotenv()

HOTMART_TOKEN = os.getenv("HOTMART_TOKEN")
BOT_VENTAS_URL = os.getenv("BOT_VENTAS_URL")

app = FastAPI(title="Bot Investigador", version="1.0")

# 🔎 Endpoint para probar
@app.get("/")
def root():
    return {"status": "ok", "message": "Bot Investigador funcionando 🚀"}

# 🔎 Ejemplo de búsqueda en Hotmart (simulado por ahora)
@app.get("/investigar/hotmart")
def investigar_hotmart():
    # Aquí iría la integración real con la API de Hotmart
    productos = [
        {"nombre": "Curso de Marketing Digital", "precio": 49.99, "link": "https://hotmart.com/curso1"},
        {"nombre": "Guía Keto Premium", "precio": 29.99, "link": "https://hotmart.com/curso2"}
    ]

    # Enviar al bot de ventas
    if BOT_VENTAS_URL:
        try:
            requests.post(BOT_VENTAS_URL, json={"productos": productos})
        except Exception as e:
            return {"status": "error", "detalle": str(e)}

    return {"status": "ok", "productos": productos}

# 🔎 Ejemplo scraping de Amazon (búsqueda básica)
@app.get("/investigar/amazon")
def investigar_amazon():
    url = "https://www.amazon.com/s?k=laptop"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        return {"status": "error", "detalle": "No se pudo acceder a Amazon"}

    soup = BeautifulSoup(resp.text, "lxml")
    titulos = [t.get_text() for t in soup.select("h2 span")[:5]]

    productos = [{"nombre": t, "precio": "N/A"} for t in titulos]

    # Enviar al bot de ventas
    if BOT_VENTAS_URL:
        try:
            requests.post(BOT_VENTAS_URL, json={"productos": productos})
        except Exception as e:
            return {"status": "error", "detalle": str(e)}

    return {"status": "ok", "productos": productos}
