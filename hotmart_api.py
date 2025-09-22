import httpx
import os

CLIENT_ID = os.getenv("HOTMART_CLIENT_ID")
CLIENT_SECRET = os.getenv("HOTMART_CLIENT_SECRET")

BASE_URL = "https://api-sec-vlc.hotmart.com"

async def obtener_productos():
    headers = {
        "Authorization": f"Basic {os.getenv('HOTMART_BASIC')}"
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/catalog/products", headers=headers)
        if r.status_code == 200:
            return r.json().get("items", [])
        return []

def filtrar_productos(productos):
    return [
        p for p in productos
        if p.get("price", 0) > 0 and p.get("commission", 0) > 0
    ]

async def afiliar_producto(product_id):
    headers = {
        "Authorization": f"Basic {os.getenv('HOTMART_BASIC')}"
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/affiliate/{product_id}", headers=headers)
        return r.status_code == 200
