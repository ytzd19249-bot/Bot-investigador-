import os
import requests
import logging

HOTMART_CLIENT_ID = os.getenv("HOTMART_CLIENT_ID")
HOTMART_CLIENT_SECRET = os.getenv("HOTMART_CLIENT_SECRET")

logger = logging.getLogger(__name__)

# ============================================
# 1. Obtener token de acceso desde Hotmart
# ============================================
def obtener_token():
    url = "https://api-sec-vlc.hotmart.com/security/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": HOTMART_CLIENT_ID,
        "client_secret": HOTMART_CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    resp = requests.post(url, data=data, headers=headers)
    if resp.status_code == 200:
        return resp.json()["access_token"]
    else:
        logger.error(f"Error al obtener token: {resp.text}")
        return None

# ============================================
# 2. Obtener productos disponibles
# ============================================
def obtener_productos():
    token = obtener_token()
    if not token:
        return []

    url = "https://developers.hotmart.com/payments/api/v1/products"
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        productos = resp.json().get("items", [])
        return productos
    else:
        logger.error(f"Error al obtener productos: {resp.text}")
        return []

# ============================================
# 3. Filtrar productos más rentables
# ============================================
def filtrar_productos(productos):
    """
    Filtra los productos para quedarse con:
    - Los que están vendiéndose (ventas activas)
    - Los que tengan comisiones positivas (aunque sean pequeñas)
    """
    filtrados = []
    for p in productos:
        try:
            ventas = p.get("sales", 0)
            comision = float(p.get("commission", 0))

            if ventas > 0 and comision > 0:
                filtrados.append({
                    "id": p.get("id"),
                    "nombre": p.get("name"),
                    "ventas": ventas,
                    "comision": comision,
                })
        except Exception as e:
            logger.error(f"Error filtrando producto: {e}")
            continue

    # Ordenar por ventas y comisión (lo más rentable arriba)
    filtrados.sort(key=lambda x: (x["ventas"], x["comision"]), reverse=True)
    return filtrados
