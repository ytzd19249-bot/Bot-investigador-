from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os
import uvicorn

from db import init_db, SessionLocal, Producto
from hotmart import investigar_productos, afiliar_producto

# Inicializar FastAPI
app = FastAPI(title="Bot Investigador")

# Inicializar base de datos
init_db()

# ========== JOB DE INVESTIGACIÓN ==========
def job_investigacion():
    print("🔎 Ejecutando investigación automática...")
    productos = investigar_productos()

    db = SessionLocal()
    try:
        for p in productos:
            # Afiliar automáticamente
            link_afiliado = afiliar_producto(p)

            producto = Producto(
                nombre=p["nombre"],
                descripcion=p["descripcion"],
                precio=p["precio"],
                moneda=p.get("moneda", "USD"),
                link=link_afiliado,
                source="Hotmart",
                activo=True,
            )
            db.add(producto)
        db.commit()
        print(f"✅ {len(productos)} productos investigados y guardados")
    except Exception as e:
        print("❌ Error en job_investigacion:", e)
        db.rollback()
    finally:
        db.close()

# ========== SCHEDULER ==========
scheduler = BackgroundScheduler()
horas = int(os.getenv("SCHEDULE_CRON_HOURS", 12))  # cada 12 horas por defecto
scheduler.add_job(job_investigacion, IntervalTrigger(hours=horas))
scheduler.start()

# ========== ENDPOINTS ==========
@app.get("/")
def root():
    return {"status": "✅ Servidor arriba", "info": "Bot Investigador corriendo"}

@app.get("/test-db")
def test_db():
    db = SessionLocal()
    try:
        productos = db.query(Producto).order_by(Producto.created_at.desc()).limit(5).all()
        return {
            "ok": True,
            "productos": [
                {
                    "id": p.id,
                    "nombre": p.nombre,
                    "precio": p.precio,
                    "moneda": p.moneda,
                    "activo": p.activo,
                }
                for p in productos
            ],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        db.close()

# ========== ARRANQUE EN RENDER ==========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
