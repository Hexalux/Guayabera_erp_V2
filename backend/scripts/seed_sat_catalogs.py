import asyncio
import sys
import os

# Añadir el directorio raíz al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal, engine
from app.models.hr import SATCatalogoPercepcion, SATCatalogoDeduccion, Base

async def seed_catalogs():
    async with engine.begin() as conn:
        print("Creando tablas si no existen...")
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as db:
        print("Seding SAT Catalogs (Percepciones)...")
        percepciones = [
            SATCatalogoPercepcion(clave="001", descripcion="Sueldos, Salarios Rayas y Jornales"),
            SATCatalogoPercepcion(clave="002", descripcion="Gratificación Anual (Aguinaldo)"),
            SATCatalogoPercepcion(clave="003", descripcion="Participación de los Trabajadores en las Utilidades PTU"),
            SATCatalogoPercepcion(clave="004", descripcion="Reembolso de Gastos Médicos Dentales y Hospitalarios"),
            SATCatalogoPercepcion(clave="005", descripcion="Fondo de Ahorro"),
            SATCatalogoPercepcion(clave="019", descripcion="Horas extra"),
            SATCatalogoPercepcion(clave="038", descripcion="Otros ingresos por salarios")
        ]
        
        for p in percepciones:
            db.add(p)
            
        print("Seding SAT Catalogs (Deducciones)...")
        deducciones = [
            SATCatalogoDeduccion(clave="001", descripcion="Seguridad social (IMSS)"),
            SATCatalogoDeduccion(clave="002", descripcion="ISR"),
            SATCatalogoDeduccion(clave="003", descripcion="Aportaciones a retiro, cesantía en edad avanzada y vejez"),
            SATCatalogoDeduccion(clave="004", descripcion="Otros (Faltas, Préstamos)"),
            SATCatalogoDeduccion(clave="006", descripcion="Descuento por incapacidad")
        ]
        
        for d in deducciones:
            db.add(d)
            
        await db.commit()
        print("Seeding completado con éxito.")

if __name__ == "__main__":
    asyncio.run(seed_catalogs())
