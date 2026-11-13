"""Web retrieval service for real-world topic grounding."""

import logging
import re
from typing import Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class VisualKnowledgeService:
    """Retrieves live web knowledge and visual context for creative generation."""

    @staticmethod
    async def retrieve_visual_knowledge(prompt: str) -> str:
        """Retrieves web knowledge and descriptors for a subject."""
        clean_prompt = prompt.strip()
        if not clean_prompt or len(clean_prompt) < 3:
            return ""

        # Check if topic is a generic greeting where search is unnecessary
        if clean_prompt.lower() in ["hello", "hi", "test", "good morning"]:
            return ""

        api_key = getattr(settings, "FIRECRAWL_API_KEY", "") or getattr(settings, "FILECRAWLER_API_KEY", "")
        if not api_key:
            logger.info("Firecrawl API key not configured. Proceeding with intrinsic LLM visual director.")
            return ""

        search_query = clean_prompt
        # Strip generic command phrases like 'create a poster for' to focus search on the core entity
        core_query = re.sub(
            r"^(create\s+(a\s+)?(poster|video|reel|creative|flyer|banner|ad)\s+(for\s+)?(the\s+)?)",
            "",
            search_query,
            flags=re.I,
        ).strip()
        if len(core_query) >= 3:
            search_query = core_query

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": search_query,
            "limit": 3,
        }

        try:
            logger.info("Querying live web visual knowledge (v2) for topic: '%s'", search_query)
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post("https://api.firecrawl.dev/v2/search", headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    snippets = []
                    data_obj = data.get("data")
                    items = []
                    if isinstance(data_obj, list):
                        items = data_obj
                    elif isinstance(data_obj, dict):
                        items = data_obj.get("web", []) or data_obj.get("results", [])

                    if items and isinstance(items, list):
                        for item in items[:3]:
                            title = item.get("title", "").strip()
                            desc = item.get("description", "").strip()
                            if title or desc:
                                snippets.append(f"• {title}: {desc}")

                    if snippets:
                        summary = "\n".join(snippets)
                        logger.info("Successfully retrieved %d real-world web insights (v2) for prompt.", len(snippets))
                        return summary
        except Exception as exc:
            logger.warning("Visual web knowledge retrieval encountered an issue: %s. Using direct director reasoning.", exc)

        return ""
