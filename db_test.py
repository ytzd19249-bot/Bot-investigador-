# db.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Set DATABASE_URL env var")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True)
    nombre = Column(String(512))
    categoria = Column(String(255), index=True)
    precio = Column(Float, nullable=True)
    comision = Column(String(50), nullable=True)
    link_afiliado = Column(Text, nullable=True)
    imagen_url = Column(Text, nullable=True)
    descripcion = Column(Text, nullable=True)
    fuente = Column(String(50), index=True)
    score = Column(Float, default=0.0)
    afiliado = Column(Boolean, default=False)
    fecha_detectado = Column(DateTime(timezone=True), server_default=func.now())

def init_db():
    Base.metadata.create_all(bind=engine)
