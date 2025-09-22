from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Leer la variable DATABASE_URL desde Render
DATABASE_URL = os.getenv("DATABASE_URL")

# Conexión a la base
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

# Modelo de tabla productos
class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    categoria = Column(String)
    precio = Column(Float)
    link_afiliado = Column(String)

# Crear las tablas si no existen
def init_db():
    Base.metadata.create_all(bind=engine)

# Guardar un producto de prueba
def guardar_producto():
    session = SessionLocal()
    nuevo_producto = Producto(
        nombre="Curso de Inteligencia Artificial",
        categoria="Educación",
        precio=49.99,
        link_afiliado="https://go.hotmart.com/abc123"
    )
    session.add(nuevo_producto)
    session.commit()
    session.close()
    print("✅ Producto de prueba guardado en la base")

if __name__ == "__main__":
    init_db()
    guardar_producto()
