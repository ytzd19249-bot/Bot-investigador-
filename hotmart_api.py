import os
import httpx
import logging

logger = logging.getLogger("hotmart_api")

HOTMART_API_URL = "https://api-sec-vlc.hotmart.com"
HOTMART_TOKEN = os.getenv("HOTMART_TOKEN", "TOKEN_DEMO")

async def obtener_productos():
    url = f"{HOTMART_API_URL}/products"
    headers = {"Authorization": f"Bearer {HOTMART_TOKEN}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            logger.error(f"Error obteniendo productos: {resp.text}")
            return []
        return resp.json().get("items", [])

def filtrar_productos(productos):
    return [
        p for p in productos
        if p.get("commissions", [{}])[0].get("value", 0) > 5
    ]

async def afiliar_producto(product_id):
    url = f"{HOTMART_API_URL}/products/{product_id}/affiliate"
    headers = {"Authorization": f"Bearer {HOTMART_TOKEN}"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers)
        if resp.status_code != 200:
            logger.error(f"Error afiliando producto {product_id}: {resp.text}")
            return None
        return resp.json().get("affiliate_link", "enlace_demo")
