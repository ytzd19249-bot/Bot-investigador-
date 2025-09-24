import os
import logging
import requests

HOTMART_API_KEY = os.getenv("HOTMART_API_KEY")
HOTMART_BASE_URL = "https://api-sec-vlc.hotmart.com"  # endpoint base de Hotmart


def fetch_hotmart_products():
    """
    Consulta productos de Hotmart.
    Retorna lista de diccionarios con info básica de productos.
    """
    url = f"{HOTMART_BASE_URL}/catalog/products"
    headers = {"Authorization": f"Bearer {HOTMART_API_KEY}"}

    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()

        products = []
        for item in data.get("items", []):
            products.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "price": item.get("price", {}).get("value"),
                "currency": item.get("price", {}).get("currency"),
                "sales_rank": item.get("sales_rank", 0),
            })
        logging.info(f"{len(products)} productos obtenidos de Hotmart.")
        return products

    except Exception as e:
        logging.error(f"Error obteniendo productos de Hotmart: {e}")
        return []


def affiliate_product(product_id: str):
    """
    Solicita link de afiliado para un producto en Hotmart.
    Retorna el enlace o None.
    """
    url = f"{HOTMART_BASE_URL}/affiliates/products/{product_id}/link"
    headers = {"Authorization": f"Bearer {HOTMART_API_KEY}"}

    try:
        r = requests.post(url, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data.get("affiliate_link")
    except Exception as e:
        logging.error(f"Error afiliando producto {product_id}: {e}")
        return None
