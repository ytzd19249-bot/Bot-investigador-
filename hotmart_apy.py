# hotmart_api.py
import os
import time
import requests
from requests.auth import HTTPBasicAuth
import logging

logger = logging.getLogger("hotmart_api")

HOT_BASE = os.getenv("HOTMART_API_BASE", "https://api-sec-vlc.hotmart.com")
CLIENT_ID = os.getenv("HOTMART_CLIENT_ID")
CLIENT_SECRET = os.getenv("HOTMART_CLIENT_SECRET")

_cached = {"token": None, "expires_at": 0}

def get_hotmart_token():
    """
    Obtener access_token desde Hotmart (client_credentials).
    Ajustar endpoint si Hotmart cambia.
    """
    now = int(time.time())
    if _cached["token"] and _cached["expires_at"] > now + 10:
        return _cached["token"]
    token_url = f"{HOT_BASE}/security/oauth/token"
    data = {"grant_type": "client_credentials"}
    try:
        resp = requests.post(token_url, data=data, auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET), timeout=15)
        resp.raise_for_status()
        j = resp.json()
        access = j.get("access_token")
        expires = int(j.get("expires_in", 3600))
        _cached["token"] = access
        _cached["expires_at"] = now + expires
        logger.info("Hotmart token obtenido, expira en %s s", expires)
        return access
    except Exception as e:
        logger.exception("Error obteniendo token Hotmart: %s", e)
        raise

def list_hotmart_products(page: int = 1, per_page: int = 50):
    """
    Listar productos públicos (ejemplo). Ajustar URL y parámetros según doc oficial.
    Retorna dict raw de la API.
    """
    token = get_hotmart_token()
    # Ejemplo endpoint (ajustar)
    url = f"{HOT_BASE}/catalog/rest/v2/products?page={page}&limit={per_page}"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def request_affiliation(product_id: str):
    """
    Intentar solicitar afiliación al producto.
    Ajustar endpoint/payload según la documentación real de Hotmart.
    """
    token = get_hotmart_token()
    url = f"{HOT_BASE}/affiliate/v1/requests"
    payload = {"product_id": product_id}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        # r.status_code puede ser 201/200 si ok; 4xx si rechazado.
        content = {}
        try:
            content = r.json()
        except Exception:
            content = {}
        return r.status_code, content
    except Exception as e:
        logger.exception("Error en request_affiliation: %s", e)
        return 0, {}
