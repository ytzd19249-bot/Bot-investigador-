# db.py
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")  # configurar en Render

if not DATABASE_URL:
    # placeholder local
    DATABASE_URL = "postgresql+psycopg2://usuario:clave@host:5432/dbname?sslmode=require"

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"sslmode": "require"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    precio = Column(Float, nullable=False, default=0.0)
    moneda = Column(String(10), nullable=False, default="USD")
    link = Column(String(1024), nullable=True)
    source = Column(String(100), nullable=True)
    source_id = Column(String(200), nullable=True, index=True)  # id en Hotmart/Amazon
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
