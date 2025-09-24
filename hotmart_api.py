# hotmart_api.py
"""
Módulo para interactuar con Hotmart.
Aquí hay funciones *simples* y comentadas. Debes completar con
las llamadas reales a la API de Hotmart usando tus credenciales.
"""

import os
import time
import random

def obtener_productos_hotmart(basic_token: str, limit: int = 50):
    """
    Debe llamar al endpoint de Hotmart que liste productos/trending.
    Por ahora devuelve mocks (ejemplo). Reemplazar con httpx/requests.
    """
    # >>> Reemplazar con llamada real a Hotmart API <<<
    # Ejemplo de salida esperada por elemento:
    # {
    #   "product_id": "hot_12345",
    #   "title": "Curso X",
    #   "description": "Curso sobre ...",
    #   "price": "29.99",
    #   "currency": "USD",
    #   "link": "https://hotmart.com/product/...",
    #   "affiliate_available": True
    # }
    resultados = []
    for i in range(min(limit, 10)):
        resultados.append({
            "product_id": f"hot_{int(time.time()) % 100000}_{i}",
            "title": f"Producto Demo {i}",
            "description": "Descripción demo",
            "price": str(10 + i*5),
            "currency": "USD",
            "link": "https://hotmart.example/demo",
            "affiliate_available": True
        })
    return resultados

def afiliar_producto_hotmart(basic_token: str, product_id: str) -> dict:
    """
    Aquí debes usar la API de Hotmart para afiliarte al producto (si aplica)
    y devolver {'affiliate_link': 'https://...tu-link...'}.
    Actualmente devuelve mock.
    """
    # >>> Reemplazar con la llamada real que hace join affiliate program <<<
    return {"affiliate_link": f"https://hotmart.affilate.mock/{product_id}?aff=TU_AFF_ID"}
