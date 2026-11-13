import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT pid, usename, datname, application_name FROM pg_stat_activity WHERE datname = 'postgres';"))
        rows = res.fetchall()
        print("Active connections to postgres db:", rows)

if __name__ == "__main__":
    asyncio.run(check())
