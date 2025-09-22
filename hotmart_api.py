import os
import requests

HOTMART_CLIENT_ID = os.getenv("HOTMART_CLIENT_ID")
HOTMART_CLIENT_SECRET = os.getenv("HOTMART_CLIENT_SECRET")
HOTMART_API_URL = "https://api-sec-vlc.hotmart.com"

def obtener_token():
    url = "https://api-sec-vlc.hotmart.com/security/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": HOTMART_CLIENT_ID,
        "client_secret": HOTMART_CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(url, data=payload, headers=headers)
    r.raise_for_status()
    return r.json().get("access_token")

def obtener_productos():
    token = obtener_token()
    url = f"{HOTMART_API_URL}/catalog/rest/v2/products"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json().get("items", [])

def filtrar_productos(productos):
    # Se queda solo con los más vendidos y los que tengan comisiones
    return [
        p for p in productos
        if p.get("commission") and p.get("salesPage")
    ]
