from fastapi import FastAPI

# Crear la app de FastAPI
app = FastAPI()

# Ruta principal para verificar que funciona
@app.get("/")
def home():
    return {"message": "🤖 Bot Investigador en Render funcionando 🚀"}

# Ruta de prueba para simular búsqueda de productos
@app.get("/buscar")
def buscar(producto: str = "ejemplo"):
    resultados = [
        {"titulo": f"{producto} Pro", "precio": "100 USD", "fuente": "Hotmart"},
        {"titulo": f"{producto} Plus", "precio": "200 USD", "fuente": "Amazon"},
    ]
    return {"resultados": resultados}
