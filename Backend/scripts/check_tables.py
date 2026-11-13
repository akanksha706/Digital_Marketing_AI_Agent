import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import engine
from sqlalchemy import text

async def list_tables():
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"))
        tables = [r[0] for r in res]
        print("TABLES IN poster_studio:", tables)

if __name__ == "__main__":
    asyncio.run(list_tables())
