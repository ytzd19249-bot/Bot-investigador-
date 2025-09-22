from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "🤖 Bot Investigador en Render funcionando 🚀"}

@app.get("/buscar")
def buscar(producto: str = "ejemplo"):
    resultados = [
        {"titulo": f"{producto} Pro", "precio": "100 USD", "fuente": "Hotmart"},
        {"titulo": f"{producto} Plus", "precio": "200 USD", "fuente": "Amazon"},
    ]
    return {"resultados": resultados}
