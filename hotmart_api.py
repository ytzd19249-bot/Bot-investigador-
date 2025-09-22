import logging
import httpx

logger = logging.getLogger("hotmart_api")

def obtener_productos():
    # Aquí va el request real a Hotmart con tu token
    productos = [
        {"id": 101, "nombre": "Curso de Marketing Digital", "precio": 49.99, "comision": 25, "estado": "activo"},
        {"id": 102, "nombre": "Guía de Recetas Veganas", "precio": 19.99, "comision": 5, "estado": "activo"},
        {"id": 103, "nombre": "Ebook Negocios Online", "precio": 9.99, "comision": 0, "estado": "inactivo"},
    ]
    return productos

def filtrar_productos(productos):
    return [p for p in productos if p["estado"] == "activo" and p["comision"] > 0]

def afiliar_producto(producto_id, token="FAKE_TOKEN"):
    """
    Simulación de afiliación en Hotmart.
    En la vida real aquí usamos el endpoint oficial con tu token.
    """
    logger.info(f"📩 Solicitando afiliación al producto {producto_id}...")
    # Simulación de respuesta positiva
    return {"status": "success", "producto_id": producto_id, "afiliado": True}
