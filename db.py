# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Cargar variables de entorno (.env)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Usar asyncpg
# Formato: postgresql+asyncpg://usuario:password@host:port/dbname
engine = create_async_engine(
    DATABASE_URL,
    echo=True,          # Pone logs en consola (quítelo si no los quiere)
    future=True
)

# Creador de sesiones asincrónicas
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency para FastAPI
async def get_db():
    async with SessionLocal() as session:
        yield session
