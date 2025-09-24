import os
import logging
import asyncio
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler
from database import save_products, get_products
from hotmart_api import fetch_hotmart_products, affiliate_product

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
SCHEDULE_CRON_HOURS = int(os.getenv("SCHEDULE_CRON_HOURS", 12))

bot = Bot(token=TELEGRAM_TOKEN)
app = FastAPI()
logging.basicConfig(level=logging.INFO)

# ---- FUNCIONES PRINCIPALES ----
async def investigator_job():
    logging.info("Ejecutando investigación en Hotmart...")

    try:
        products = fetch_hotmart_products()

        best_products = []
        for product in products:
            if product.get("sales_rank", 0) > 80:  # ejemplo de filtro
                aff_link = affiliate_product(product["id"])
                if aff_link:
                    product["affiliate_link"] = aff_link
                    best_products.append(product)

        if best_products:
            save_products(best_products)
            logging.info(f"{len(best_products)} productos guardados en DB.")
        else:
            logging.info("No se encontraron productos destacados.")

    except Exception as e:
        logging.error(f"Error en investigator_job: {e}")


# ---- COMANDOS ADMIN ----
async def admin_report(update, context):
    if context.args and context.args[0] == ADMIN_TOKEN:
        products = get_products(limit=10)
        if not products:
            await update.message.reply_text("No hay productos registrados aún.")
            return

        msg = "📊 Últimos productos investigados:\n\n"
        for p in products:
            msg += f"- {p['name']} | {p['affiliate_link']}\n"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❌ Acceso denegado.")


# ---- TELEGRAM APP ----
telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
telegram_app.add_handler(CommandHandler("report", admin_report))


# ---- SCHEDULER ----
scheduler = AsyncIOScheduler()
scheduler.add_job(
    investigator_job,
    IntervalTrigger(hours=SCHEDULE_CRON_HOURS),
    id="investigator_job",
    replace_existing=True,
)
scheduler.start()


# ---- FASTAPI ----
@app.on_event("startup")
async def on_startup():
    logging.info("Bot Investigador iniciado.")
    asyncio.create_task(telegram_app.run_polling())
