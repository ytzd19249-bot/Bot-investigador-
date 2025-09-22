import os
import requests
import logging

logger = logging.getLogger(__name__)

HOTMART_CLIENT_ID = os.getenv("HOTMART_CLIENT_ID")
HOTMART_CLIENT_SECRET = os.getenv("HOTMART_CLIENT_SECRET")

ACCESS_TOKEN = None  # token en memoria

def autenticar():
    """
    Autentica en la API de Hotmart y devuelve el access_token.
    """
    global ACCESS_TOKEN
    url = "https://api-sec-vlc.hotmart.com/security/oauth/token"
    payload = {
        "client_id": HOTMART_CLIENT_ID,
        "client_secret": HOTMART_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    try:
        r = requests.post(url, data=payload)
        r.raise_for_status()
        ACCESS_TOKEN = r.json()["access_token"]
        logger.info("✅ Autenticado con Hotmart correctamente")
        return ACCESS_TOKEN
    except Exception as e:
        logger.error(f"❌ Error autenticando en Hotmart: {e}")
        return None

def obtener_productos():
    """
    Consulta productos en Hotmart.
    """
    global ACCESS_TOKEN
    if not ACCESS_TOKEN:
        autenticar()

    url = "https://api-sec-vlc.hotmart.com/catalog/v3/products"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        productos = r.json().get("items", [])
        logger.info(f"📦 {len(productos)} productos obtenidos")
        return productos
    except Exception as e:
        logger.error(f"❌ Error obteniendo productos: {e}")
        return []

def filtrar_productos(productos):
    """
    Filtra productos con ventas y comisión atractiva.
    """
    filtrados = []
    for p in productos:
        ventas = p.get("sales", 0)
        comision = p.get("commission", {}).get("value", 0)

        if ventas > 10 and comision >= 5:  # Ajustable
            filtrados.append({
                "nombre": p.get("name"),
                "ventas": ventas,
                "comision": comision
            })

    logger.info(f"✅ {len(filtrados)} productos filtrados")
    return filtrados
