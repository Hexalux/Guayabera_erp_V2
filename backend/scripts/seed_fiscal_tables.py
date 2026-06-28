import asyncio
import sys
import os

# Añadir el directorio raíz al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal, engine
from app.models.hr import ParametroFiscal, TablaISR, Base

async def seed_fiscal_tables():
    async with engine.begin() as conn:
        print("Creando tablas fiscales si no existen...")
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as db:
        print("Seding Parametros Fiscales (UMA 2024)...")
        param = ParametroFiscal(
            anio=2024,
            uma=108.57,
            smi=248.93
        )
        db.add(param)
        
        print("Seding Tabla ISR Quincenal 2024...")
        # Límite Inferior, Límite Superior, Cuota Fija, Porcentaje
        rangos_quincenales = [
            (0.01, 368.10, 0.00, 1.92),
            (368.11, 3124.35, 7.05, 6.40),
            (3124.36, 5490.75, 183.45, 10.88),
            (5490.76, 6382.80, 441.00, 16.00),
            (6382.81, 7641.90, 583.65, 17.92),
            (7641.91, 15412.80, 809.25, 21.36),
            (15412.81, 24222.30, 2469.15, 23.52),
            (24222.31, 46232.85, 4541.55, 30.00),
            (46232.86, 61643.70, 11144.70, 32.00),
            (61643.71, 184931.25, 16076.25, 34.00),
            (184931.26, 9999999.99, 57993.90, 35.00)
        ]
        
        for li, ls, cf, p in rangos_quincenales:
            db.add(TablaISR(
                anio=2024,
                periodicidad="04", # Quincenal
                limite_inferior=li,
                limite_superior=ls,
                cuota_fija=cf,
                porcentaje=p
            ))
            
        try:
            await db.commit()
            print("Seeding completado con éxito.")
        except Exception as e:
            print(f"Error o ya existen: {e}")

if __name__ == "__main__":
    asyncio.run(seed_fiscal_tables())
