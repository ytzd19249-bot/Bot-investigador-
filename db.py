# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from models import Base, Producto

# La variable DATABASE_URL la debe configurar en Render con el External Database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está configurada en las variables de entorno")

# Engine y session
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def init_db():
    """Crear tablas si no existen."""
    Base.metadata.create_all(bind=engine)
    print("DB inicializada (tablas creadas si no existían)")

def guardar_producto(producto_data: dict):
    """
    Guarda o actualiza (upsert) un producto en la base de datos.
    producto_data debe tener al menos: id, nombre. Otros campos opcionales: precio, comision, moneda, categoria
    """
    session = SessionLocal()
    try:
        producto = Producto(
            id=str(producto_data.get("id")),
            nombre=producto_data.get("nombre") or "Sin nombre",
            precio=_to_float(producto_data.get("precio")),
            comision=_to_float(producto_data.get("comision")),
            moneda=producto_data.get("moneda"),
            categoria=producto_data.get("categoria")
        )
        # merge hace insert o update según la PK
        session.merge(producto)
        session.commit()
        return producto
    except SQLAlchemyError as e:
        session.rollback()
        print("Error guardando producto:", e)
        raise
    finally:
        session.close()

def _to_float(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None
