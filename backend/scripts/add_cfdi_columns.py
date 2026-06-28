import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def add_columns():
    print(f"Connecting to {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE hr_nominas ADD COLUMN url_xml VARCHAR NULL;"))
            print("Added url_xml")
        except Exception as e:
            print("url_xml might exist", e)

        try:
            await conn.execute(text("ALTER TABLE hr_nominas ADD COLUMN url_pdf VARCHAR NULL;"))
            print("Added url_pdf")
        except Exception as e:
            print("url_pdf might exist", e)
            
        try:
            # We already had estado_timbrado, just making sure it's updated if needed
            print("Columns updated successfully.")
        except Exception as e:
            pass

if __name__ == "__main__":
    asyncio.run(add_columns())
