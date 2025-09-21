from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# 🔑 Token admin para validar actualizaciones
ADMIN_TOKEN = "miclaveadmin"

# Catálogo dinámico en memoria
products = {}

@app.route("/")
def home():
    return "🤖 Bot Investigador corriendo!"

# Endpoint para el Bot de Ventas (pedir productos)
@app.route("/products", methods=["GET"])
def get_products():
    return jsonify(products)

# Endpoint para actualizar catálogo (usado solo por admin)
@app.route("/admin/update_products", methods=["POST"])
def update_products():
    token = request.headers.get("x-admin-token")
    if token != ADMIN_TOKEN:
        return jsonify({"error": "Acceso no autorizado"}), 403

    data = request.get_json()
    products.update(data)
    return jsonify({"status": "ok", "products": products})

# 🔹 Futuro: aquí va el scraper/investigador de Hotmart y Amazon
# Ejemplo de producto simulado:
def fetch_hotmart_products():
    return {
        "10": {
            "title": "Curso Hotmart X",
            "price": "30",
            "currency": "USD",
            "link": "https://hotmart.link/xxxx",
            "source": "Hotmart"
        }
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
