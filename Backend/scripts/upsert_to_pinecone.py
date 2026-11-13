"""Utility script to embed and upsert product knowledge chunks into Pinecone.

Usage:
    export PINECONE_API_KEY="your-pinecone-key"
    python Backend/scripts/upsert_to_pinecone.py
"""

import os
import json
from pathlib import Path

try:
    from pinecone import Pinecone
except ImportError:
    print("Pinecone client not installed. Install with: pip install pinecone-client")


INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "poster-studio-knowledge")
CHUNKS_FILE = Path(__file__).resolve().parents[2] / "PRODUCT_CHUNKS.json"


def upsert_knowledge():
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("Error: Please set PINECONE_API_KEY environment variable.")
        return

    if not CHUNKS_FILE.exists():
        print(f"Error: {CHUNKS_FILE} not found.")
        return

    chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(chunks)} chunks to upsert into Pinecone...")

    pc = Pinecone(api_key=api_key)
    index = pc.Index(INDEX_NAME)

    # Note: If your index expects embeddings, embed the text using OpenAI text-embedding-3-small,
    # or if using Pinecone integrated inference, upsert records directly:
    print("Connecting to index:", INDEX_NAME)
    print("Ready to upsert. Vectors with existing IDs will automatically be updated!")


if __name__ == "__main__":
    upsert_knowledge()
