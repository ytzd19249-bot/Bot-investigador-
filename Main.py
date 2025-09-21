from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok", "message": "Bot Investigador corriendo en Render"}

@app.get("/investigar/amazon")
def investigar_amazon():
    # Aquí en el futuro vas a poner scraping o API
    return {"fuente": "Amazon", "productos": []}

@app.get("/investigar/hotmart")
def investigar_hotmart():
    # Aquí luego conectamos con la API de Hotmart
    return {"fuente": "Hotmart", "productos": []}
