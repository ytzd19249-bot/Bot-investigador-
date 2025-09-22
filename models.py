# models.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    producto_id = Column(String, unique=True, nullable=False)  # id del producto Hotmart
    nombre = Column(String, nullable=False)
    precio = Column(Float, nullable=True)
    moneda = Column(String, nullable=True)
    comision = Column(Float, nullable=True)
    ventas = Column(Integer, nullable=True)
    link_afiliado = Column(String, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
