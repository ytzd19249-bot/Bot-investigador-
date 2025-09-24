# db.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# URL de la base de datos (Render la da en "External Database URL")
DATABASE_URL = os.getenv("DATABASE_URL")

# agregar sslmode=require para Render
if DATABASE_URL and "sslmode" not in DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        # Render a veces da postgres:// pero SQLAlchemy necesita postgresql://
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    DATABASE_URL += "?sslmode=require"

# motor de conexión
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# base declarativa
Base = declarative_base()

# Modelo de productos
class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    precio = Column(Float, nullable=True)
    moneda = Column(String(10), default="USD")
    link = Column(String(500), nullable=True)  # enlace de afiliado
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Inicializar DB
def init_db():
    Base.metadata.create_all(bind=engine)
