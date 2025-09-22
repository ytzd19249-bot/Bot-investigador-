# models.py
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Float, DateTime
from datetime import datetime

Base = declarative_base()

class Producto(Base):
    __tablename__ = "productos"
    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    precio = Column(Float, nullable=True)
    comision = Column(Float, nullable=True)
    moneda = Column(String, nullable=True)
    categoria = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
