import asyncio
from sqlalchemy import text
from app.core.database import async_session_maker
from app.models.admin import Admin
from sqlalchemy import select

async def test_db():
    try:
        async with async_session_maker() as session:
            # Test simple query
            await session.execute(text("SELECT 1"))
            print("DB Connection OK")
            
            # Test admins table
            result = await session.execute(select(Admin))
            admins = result.scalars().all()
            print(f"Admins table queried OK. Found {len(admins)} admins.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_db())
