import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import engine
from sqlalchemy import text

async def update_pw():
    async with engine.begin() as conn:
        await conn.execute(text("ALTER USER postgres WITH PASSWORD '42works123';"))
        print("SUCCESS: PostgreSQL password changed to '42works123'")

if __name__ == "__main__":
    asyncio.run(update_pw())
