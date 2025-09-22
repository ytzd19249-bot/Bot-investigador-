from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    precio = Column(Float, nullable=True)
    comision = Column(Float, nullable=True)
    link = Column(String, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def guardar_producto(nombre, precio, comision, link):
    db = SessionLocal()
    producto = Producto(
        nombre=nombre,
        precio=precio,
        comision=comision,
        link=link
    )
    db.add(producto)
    db.commit()
    db.close()
