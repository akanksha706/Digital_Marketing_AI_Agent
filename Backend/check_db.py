import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "Backend"))

from app.db.session import async_session_factory
from app.db.models import Poster
from sqlalchemy import select

async def main():
    async with async_session_factory() as db:
        res = await db.execute(select(Poster).order_by(Poster.id.desc()).limit(3))
        for p in res.scalars():
            print(f"ID: {p.id} | Video: {p.video_url} | Headline: {p.headline} | Layout: {p.layout_meta}")

if __name__ == "__main__":
    asyncio.run(main())
