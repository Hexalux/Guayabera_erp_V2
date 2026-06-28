import asyncio
import sys
import os

# Asegurar que el backend esté en el path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import engine
from sqlalchemy import text

async def drop_tables():
    async with engine.begin() as conn:
        print("Dropping tables...")
        await conn.execute(text("DROP TABLE IF EXISTS notas_credito_proveedor CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS pagos_cxp CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS cuentas_por_pagar CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS detalles_orden_compra CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS ordenes_compra CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS proveedores CASCADE;"))
        print("Tables dropped successfully!")

if __name__ == "__main__":
    asyncio.run(drop_tables())
