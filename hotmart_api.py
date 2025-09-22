# hotmart_api.py
import os
import httpx
import asyncio
import logging

logger = logging.getLogger("hotmart_api")
logger.setLevel(logging.INFO)

HOTMART_API_BASE = "https://api-sec-vlc.hotmart.com"
CLIENT_ID = os.getenv("HOTMART_CLIENT_ID")
CLIENT_SECRET = os.getenv("HOTMART_CLIENT_SECRET")
BASIC = os.getenv("HOTMART_BASIC")  # opcional

async def obtener_token():
    """
    Obtiene token OAuth2 client_credentials desde Hotmart.
    """
    url = f"{HOTMART_API_BASE}/security/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    # si tiene BASIC, lo puede usar en Authorization header (opcional)
    if BASIC:
        headers["Authorization"] = BASIC

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, data=data, headers=headers)
        r.raise_for_status()
        return r.json().get("access_token")

async def obtener_productos():
    """
    Consulta productos. Devuelve lista de productos (raw).
    Nota: endpoint exacto puede variar según cuenta Hotmart; este es un ejemplo.
    """
    try:
        token = await obtener_token()
    except Exception as e:
        logger.error("No se pudo obtener token Hotmart: %s", e)
        return []

    # Endpoint usado como ejemplo — ajústelo si su cuenta usa otra ruta
    url = f"{HOTMART_API_BASE}/catalog/v3/products"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers)
        if r.status_code != 200:
            logger.error("Error al obtener productos Hotmart: %s %s", r.status_code, r.text)
            return []
        data = r.json()
        # Normalizar: algunos endpoints devuelven 'items', 'data', etc.
        productos = data.get("items") or data.get("data") or data.get("products") or []
        return productos

def filtrar_productos(productos, min_comision=1.0):
    """
    Filtra productos básicos:
    - que estén activos,
    - que tengan comisión > min_comision
    - (puede ajustarse el criterio)
    """
    filtrados = []
    for p in productos:
        try:
            # varios proveedores usan distintos nombres; intentamos ser tolerantes
            nombre = p.get("name") or p.get("title") or p.get("nombre")
            product_id = str(p.get("id") or p.get("productId") or p.get("product_id") or "")
            # comisión aproximada (intentar leer varios campos)
            comision = None
            if isinstance(p.get("commission"), dict):
                comision = float(p["commission"].get("value", 0))
            else:
                comision = float(p.get("commission", p.get("commission_percentage", 0) or 0))
            estado = p.get("status") or p.get("state") or p.get("statusType") or "activo"
            ventas = int(p.get("sales", p.get("sales_total", 0) or 0))
            link = p.get("salesPage") or p.get("sales_page") or p.get("sales_url") or p.get("link") or ""

            if not product_id:
                continue
            if comision is None:
                comision = 0.0

            # criterio: activo y comisión positiva (puede ajustar min_comision)
            if (str(estado).lower() in ("active", "activo", "published", "available")) and comision >= min_comision:
                filtrados.append({
                    "id": product_id,
                    "nombre": nombre,
                    "comision": comision,
                    "ventas": ventas,
                    "link": link
                })
        except Exception as e:
            logger.warning("Error procesando producto: %s", e)
            continue

    # Ordenar por ventas y comisión (más interesantes arriba)
    filtrados.sort(key=lambda x: (x.get("ventas", 0), x.get("comision", 0)), reverse=True)
    logger.info("Filtrados encontrados: %d", len(filtrados))
    return filtrados

async def afiliar_producto(product_id: str):
    """
    Intenta afiliarse al producto. Endpoint ejemplo (ajustar si Hotmart cambia).
    Devuelve dict con status y detalle.
    """
    try:
        token = await obtener_token()
    except Exception as e:
        logger.error("No token para afiliar: %s", e)
        return {"ok": False, "detail": "no_token"}

    # Nota: endpoint de afiliación puede variar. Este es un ejemplo genérico.
    url = f"{HOTMART_API_BASE}/catalog/v3/products/{product_id}/affiliations"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, headers=headers, json={})
        # algunos endpoints devuelven 201 o 200
        if r.status_code in (200,201):
            logger.info("Afiliación solicitada OK para %s", product_id)
            return {"ok": True, "detail": r.json()}
        else:
            logger.warning("Afiliación falló %s -> %s", product_id, r.text[:300])
            return {"ok": False, "detail": r.text}
