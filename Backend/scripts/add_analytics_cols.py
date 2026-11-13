import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import engine
from sqlalchemy import text

async def migrate():
    async with engine.begin() as conn:
        # Check current columns
        res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'posters';"))
        existing_cols = {row[0] for row in res}
        print("Existing columns in posters:", existing_cols)

        if "is_archived" not in existing_cols:
            print("Adding is_archived column...")
            await conn.execute(text("ALTER TABLE posters ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT FALSE;"))
            print("Added is_archived.")
        else:
            print("is_archived already exists.")

        if "published_at" not in existing_cols:
            print("Adding published_at column...")
            await conn.execute(text("ALTER TABLE posters ADD COLUMN published_at TIMESTAMP WITH TIME ZONE NULL;"))
            print("Added published_at.")
        else:
            print("published_at already exists.")

        # Also let's check scheduled_jobs table for target platform and execution
        jobs_res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'scheduled_jobs';"))
        jobs_cols = {row[0] for row in jobs_res}
        print("Existing columns in scheduled_jobs:", jobs_cols)

if __name__ == "__main__":
    asyncio.run(migrate())
