import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Producto

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bot.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def guardar_producto(data):
    session = SessionLocal()
    producto = Producto(
        id=data["id"],
        name=data["name"],
        price=data.get("price", 0),
        commission=data.get("commissions", [{}])[0].get("value", 0),
        affiliate_link=data.get("affiliate_link", "")
    )
    session.merge(producto)
    session.commit()
    session.close()
