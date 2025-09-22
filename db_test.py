# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Producto
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("Falta DATABASE_URL en variables de entorno")

# engine sync (sencillo y compatible)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def guardar_producto(data: dict):
    """
    Inserta o actualiza producto en DB (merge por producto_id).
    data debe traer: id, nombre, precio, moneda, comision, ventas, link
    """
    session = SessionLocal()
    try:
        producto = session.query(Producto).filter(Producto.producto_id == str(data["id"])).first()
        if not producto:
            producto = Producto(
                producto_id=str(data["id"]),
                nombre=data.get("nombre"),
                precio=data.get("precio"),
                moneda=data.get("moneda"),
                comision=data.get("comision"),
                ventas=data.get("ventas"),
                link_afiliado=data.get("link") or data.get("link_afiliado")
            )
            session.add(producto)
        else:
            producto.nombre = data.get("nombre", producto.nombre)
            producto.precio = data.get("precio", producto.precio)
            producto.comision = data.get("comision", producto.comision)
            producto.ventas = data.get("ventas", producto.ventas)
            producto.link_afiliado = data.get("link", producto.link_afiliado)
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
