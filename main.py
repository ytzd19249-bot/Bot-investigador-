from fastapi import FastAPI
import uvicorn

# Crear la app
app = FastAPI()

# Ruta principal
@app.get("/")
def home():
    return {"message": "🤖 Bot Investigador está activo y funcionando!"}

# Otra ruta de ejemplo
@app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}

# Esto es útil si corres el bot localmente (ej: python main.py)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=True)
