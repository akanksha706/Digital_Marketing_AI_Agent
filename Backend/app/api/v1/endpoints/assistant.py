"""Assistant chat endpoint powered by Pinecone RAG and Cloudflare LLaMA 3.1."""

import re
from fastapi import APIRouter
from pydantic import BaseModel, Field
import httpx
import logging
from pinecone import Pinecone
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assistant", tags=["Studio Assistant"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(payload: ChatRequest):
    """Answers user queries in friendly layman terms using Pinecone knowledge retrieval + LLaMA 3.1."""
    user_query = payload.message.strip()

    # 1. Retrieve top matching layman chunks from Pinecone
    context_text = ""
    try:
        if settings.PINECONE_API_KEY:
            pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            index = pc.Index(settings.PINECONE_INDEX_NAME)
            search_res = index.search_records(
                namespace="studio_docs",
                query={"inputs": {"text": user_query}, "top_k": 3},
            )
            hits = search_res.get("result", {}).get("hits", [])
            retrieved_chunks = [h.get("fields", {}).get("text", "") for h in hits if h.get("fields")]
            if retrieved_chunks:
                context_text = "\n\n".join(retrieved_chunks)
    except Exception as e:
        logger.warning(f"Pinecone retrieval failed: {e}")

    # 2. Ask Cloudflare LLaMA 3.1 to answer warmly in layman terms
    system_prompt = (
        "You are 'Pickachoo' (Sparky), the friendly, cheerful, and knowledgeable assistant for 42 WORKS AI Poster & Social Content Studio. "
        "Your job is to answer user questions about the product clearly, warmly, and in simple everyday layman terms. "
        "Keep your answer concise (2 to 4 sentences), easy to understand for beginners, in plain text without emojis or special symbol characters. "
        "Guide the user step-by-step on where to click or what to do.\n\n"
        f"OFFICIAL PRODUCT KNOWLEDGE BASE:\n{context_text}"
    )

    headers = {
        "Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    llm_payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
        "max_tokens": 300,
    }

    endpoint = (
        f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/ai/run/{settings.TEXT_MODEL}"
    )

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(endpoint, headers=headers, json=llm_payload)
            resp.raise_for_status()
            data = resp.json()
            reply = data.get("result", {}).get("response", "").strip()
            if reply:
                # Remove encoding corruption artifacts and stray surrogate representations
                reply = re.sub(r'd\?+', '', reply)
                reply = re.sub(r'[\?\s]*d\?+[\?\s]*', ' ', reply)
                reply = reply.strip()
                return ChatResponse(reply=reply)
    except Exception as e:
        logger.warning(f"LLM assistant call failed: {e}")

    # Fallback to retrieved text if network is slow
    if context_text:
        first_line = context_text.split(". ")[0] + "."
        return ChatResponse(reply=first_line)

    return ChatResponse(
        reply="Hi! You can create posters in the Studio tab, customize them in the review window, and publish directly to LinkedIn and Instagram! ✨"
    )
