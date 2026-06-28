import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import engine
from sqlalchemy import text

async def fix_db():
    async with engine.begin() as conn:
        print("Fixing tables...")
        # Check if table exists, then alter
        await conn.execute(text("""
            DO $$ 
            BEGIN 
                -- Drop the problematic table so create_all can recreate it
                DROP TABLE IF EXISTS public.notas_credito_proveedor CASCADE;
                
                -- Alter cuentas_por_pagar id to VARCHAR
                IF EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'cuentas_por_pagar' AND column_name = 'id') THEN
                    ALTER TABLE public.cuentas_por_pagar ALTER COLUMN id TYPE VARCHAR USING id::text;
                END IF;
                
                IF EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'pagos_cxp' AND column_name = 'cuenta_por_pagar_id') THEN
                    ALTER TABLE public.pagos_cxp ALTER COLUMN cuenta_por_pagar_id TYPE VARCHAR USING cuenta_por_pagar_id::text;
                END IF;
            END $$;
        """))
        print("DB Fixed!")

if __name__ == "__main__":
    asyncio.run(fix_db())
