import logging
from db import SessionLocal, Producto
from hotmart_api import fetch_hotmart_products, affiliate_product


def run_investigation():
    """
    Corre el flujo de investigación → afiliación → guardar en DB.
    """
    db = SessionLocal()
    try:
        productos = fetch_hotmart_products(limit=50)
        if not productos:
            logging.warning("⚠️ No se encontraron productos en Hotmart.")
            return

        for p in productos[:20]:  # top 20 más vendidos
            # afiliar producto
            link_afiliado = affiliate_product(p["id"])
            if not link_afiliado:
                logging.info(f"No se pudo afiliar {p['nombre']}")
                continue

            # revisar si ya está en la DB
            prod = db.query(Producto).filter(Producto.id_externo == str(p["id"])).first()
            if prod:
                # actualizar
                prod.nombre = p["nombre"]
                prod.precio = p["precio"]
                prod.moneda = p["moneda"]
                prod.link = link_afiliado
                prod.activo = True
                logging.info(f"🔄 Producto actualizado: {p['nombre']}")
            else:
                # crear nuevo
                prod = Producto(
                    id_externo=str(p["id"]),
                    nombre=p["nombre"],
                    precio=p["precio"],
                    moneda=p["moneda"],
                    link=link_afiliado,
                    activo=True,
                )
                db.add(prod)
                logging.info(f"✅ Producto agregado: {p['nombre']}")

        db.commit()
        logging.info("🚀 Investigación completada con éxito.")

    except Exception as e:
        logging.error(f"Error en investigación: {e}")
    finally:
        db.close()
