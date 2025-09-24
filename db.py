from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL")

# Forzar SSL en Render si no viene en la URL
if DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

# SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False)

# Sesión
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base declarativa
Base = declarative_base()

# Modelo Producto
class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    precio = Column(Float)
    moneda = Column(String, default="USD")
    link = Column(String)
    source = Column(String)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Inicializar DB
def init_db():
    Base.metadata.create_all(bind=engine)
