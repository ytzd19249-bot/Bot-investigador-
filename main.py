import logging
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from hotmart_api import obtener_productos, filtrar_productos, afiliar_producto

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI()
scheduler = AsyncIOScheduler()

def investigar_hotmart():
    logger.info("🔎 Iniciando investigación automática de productos...")
    productos = obtener_productos()
    seleccionados = filtrar_productos(productos)

    if seleccionados:
        for p in seleccionados:
            logger.info(f"✅ Producto válido: {p['nombre']} | Precio: {p['precio']} | Comisión: {p['comision']}")
            resultado = afiliar_producto(p["id"])
            if resultado["afiliado"]:
                logger.info(f"🤝 Afiliación exitosa al producto {p['nombre']}")
            else:
                logger.warning(f"⚠️ No se pudo afiliar al producto {p['nombre']}")
    else:
        logger.warning("⚠️ No se encontraron productos válidos en esta ejecución.")

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(investigar_hotmart, "cron", hour="9,18")  # 2 veces al día
    scheduler.start()
    logger.info("🚀 Bot Investigador iniciado. Ejecutando automáticamente 2 veces al día.")
