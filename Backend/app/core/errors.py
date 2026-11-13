"""User-facing error sanitization utilities."""

import logging
import re

logger = logging.getLogger(__name__)


def to_user_friendly_error(exc: Exception, context: str = "creative generation") -> str:
    """Translates raw technical exceptions into friendly UI messages while preserving logs."""
    raw = str(exc)
    raw_lower = raw.lower()

    # 1. Content moderation & safety warnings
    if "content moderation" in raw_lower or "safety" in raw_lower or "banned word" in raw_lower:
        clean = re.sub(r"^(content moderation warning|error):\s*", "", raw, flags=re.I).strip()
        return clean or "Your prompt contains content that could not be processed under our brand safety guidelines."

    # 2. Rate limit / quota / high load
    if "429" in raw_lower or "too many requests" in raw_lower or "quota" in raw_lower or "neurons" in raw_lower:
        return "The creative AI service is temporarily experiencing high traffic. Please wait a moment and try again."

    # 3. Timeouts / network delays
    if "timeout" in raw_lower or "timed out" in raw_lower or "connecterror" in raw_lower:
        return "The request took longer than expected due to network latency. Please try again in a few moments."

    # 4. Image reading / invalid formats
    if "cannot identify image" in raw_lower or "invalid image" in raw_lower or "unsupported image" in raw_lower:
        return "Unable to process the uploaded image. Please ensure it is a standard JPG, PNG, or WEBP file."

    # 5. Missing / not found resources
    if "not found" in raw_lower or "404" in raw_lower:
        return f"The requested {context} asset could not be located. It may have been moved or removed."

    # 6. Database / validation errors
    if "integrityerror" in raw_lower or "foreignkey" in raw_lower or "unique constraint" in raw_lower:
        return f"Unable to save your changes to the {context}. Please verify your input and try again."

    # 7. Default friendly fallback
    return f"We encountered a temporary issue while processing your {context}. Please try again shortly."
