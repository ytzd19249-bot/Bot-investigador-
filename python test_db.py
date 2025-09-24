# test_db.py
from db import SessionLocal, Producto, init_db

def test_insert_and_list():
    # Inicializa DB (crea tablas si no existen)
    init_db()
    db = SessionLocal()

    try:
        # Insertar un producto de prueba
        producto = Producto(
            nombre="Curso Prueba Investigador",
            descripcion="Producto de prueba insertado desde test_db.py",
            precio="49.99",
            moneda="USD",
            link="https://hotmart.com/producto-prueba",
            activo=True,
        )
        db.add(producto)
        db.commit()
        db.refresh(producto)

        print("✅ Insertado:", producto.id, producto.nombre)

        # Listar últimos productos
        productos = db.query(Producto).order_by(Producto.created_at.desc()).limit(5).all()
        print("📦 Últimos productos en DB:")
        for p in productos:
            print(f"- {p.id}: {p.nombre} | {p.precio} {p.moneda} | activo={p.activo}")

    except Exception as e:
        print("❌ Error en la prueba:", e)
    finally:
        db.close()

if __name__ == "__main__":
    test_insert_and_list()
