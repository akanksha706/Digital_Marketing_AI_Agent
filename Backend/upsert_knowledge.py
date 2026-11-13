"""Permanent script to upload or update product knowledge into Pinecone vector DB.

Usage:
    cd Backend
    .venv\\Scripts\\python upsert_knowledge.py
"""

import sys
import json
import time
from pathlib import Path

# Ensure Backend directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pinecone import Pinecone
from app.core.config import settings


def main():
    if not settings.PINECONE_API_KEY:
        print("Error: PINECONE_API_KEY is not set in Backend/.env")
        return

    index_name = settings.PINECONE_INDEX_NAME or "poster-studio-knowledge"
    print(f"Connecting to Pinecone index: '{index_name}'...")

    pc = Pinecone(api_key=settings.PINECONE_API_KEY)

    # Check if index exists, create if not
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing_indexes:
        print(f"Index '{index_name}' not found. Creating serverless index with integrated embeddings...")
        pc.create_index_for_model(
            name=index_name,
            cloud="aws",
            region="us-east-1",
            embed={
                "model": "multilingual-e5-large",
                "metric": "cosine",
                "field_map": {"text": "text"},
            },
        )
        print("Waiting for index to become ready...")
        for _ in range(30):
            desc = pc.describe_index(index_name)
            if desc.status["ready"]:
                break
            time.sleep(2)
        print("Index is ready!")

    index = pc.Index(index_name)

    # Locate chunks file in project root
    chunks_path = Path(__file__).resolve().parents[1] / "PRODUCT_CHUNKS.json"
    if not chunks_path.exists():
        print(f"Error: {chunks_path} not found.")
        return

    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    records = []
    for c in chunks:
        records.append({
            "_id": c["id"],
            "text": f"{c['title']}: {c['text']}",
            "section": c["section"],
            "title": c["title"],
        })

    print(f"Upserting {len(records)} product knowledge chunks into Pinecone (namespace: 'studio_docs')...")
    index.upsert_records(namespace="studio_docs", records=records)
    print("Upsert completed successfully!")

    time.sleep(2)
    stats = index.describe_index_stats()
    print("Pinecone Index Stats:", stats)


if __name__ == "__main__":
    main()
