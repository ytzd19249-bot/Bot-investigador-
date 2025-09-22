import os
import httpx
import asyncio

HOTMART_API_URL = "https://api-sec-vlc.hotmart.com"
CLIENT_ID = os.getenv("HOTMART_CLIENT_ID")
CLIENT_SECRET = os.getenv("HOTMART_CLIENT_SECRET")
BASIC_TOKEN = os.getenv("HOTMART_BASIC")

# =====================================================
# 🔑 Obtener token de acceso
# =====================================================
async def obtener_token():
    url = f"{HOTMART_API_URL}/security/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    headers = {"Authorization": BASIC_TOKEN}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data, headers=headers)
        response.raise_for_status()
        return response.json()["access_token"]

# =====================================================
# 📦 Obtener productos
# =====================================================
async def obtener_productos():
    token = await obtener_token()
    url = f"{HOTMART_API_URL}/catalog/products"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("items", [])

# =====================================================
# 🔎 Filtrar productos por ventas y comisiones
# =====================================================
def filtrar_productos(productos):
    filtrados = []
    for p in productos:
        comision = p.get("commission", 0)
        ventas = p.get("sales", 0)

        if comision >= 10 and ventas > 0:
            filtrados.append({
                "id": p.get("id"),
                "nombre": p.get("name"),
                "comision": comision,
                "ventas": ventas
            })
    return filtrados

# =====================================================
# 🤝 Afiliarse a un producto
# =====================================================
async def afiliar_producto(producto_id: int):
    """
    Simula el proceso de afiliación a un producto de Hotmart.
    En la versión real se debe usar el endpoint oficial de Hotmart.
    """
    print(f"📩 Solicitando afiliación al producto {producto_id}...")
    await asyncio.sleep(1)  # Simulación
    print(f"✅ Afiliación exitosa al producto {producto_id}")
    return True
