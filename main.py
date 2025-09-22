import os
import asyncio
from fastapi import FastAPI, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from hotmart_api import obtener_productos, filtrar_productos, afiliar_producto

app = FastAPI()

# =====================================================
# 🔁 Tarea principal del bot investigador
# =====================================================
async def investigar_hotmart():
    print("🔎 Iniciando investigación de productos...")

    try:
        productos = await obtener_productos()
        print(f"📦 Productos encontrados: {len(productos)}")

        seleccionados = filtrar_productos(productos)
        print(f"✅ Productos filtrados: {len(seleccionados)}")

        for producto in seleccionados:
            producto_id = producto["id"]
            nombre = producto["nombre"]
            comision = producto["comision"]
            ventas = producto["ventas"]

            print(f"➡️ Producto elegido: {nombre} | Comisión: {comision} | Ventas: {ventas}")

            # Afiliación automática
            afiliado = await afiliar_producto(producto_id)
            if afiliado:
                print(f"🤝 Afiliado al producto {producto_id} ({nombre})")

    except Exception as e:
        print(f"❌ Error en investigación: {e}")

# =====================================================
# ⏰ Scheduler para ejecutar la investigación automáticamente
# =====================================================
scheduler = AsyncIOScheduler()
scheduler.add_job(investigar_hotmart, "interval", hours=12)  # 2 veces al día
scheduler.start()

# =====================================================
# 🌐 Endpoint raíz
# =====================================================
@app.get("/")
async def root():
    return {"status": "Bot Investigador funcionando 🚀"}

# =====================================================
# 📩 Webhook (para Telegram u otros si se necesita después)
# =====================================================
@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    data = await request.json()
    print(f"📩 Webhook recibido: {data}")
    return {"ok": True}
