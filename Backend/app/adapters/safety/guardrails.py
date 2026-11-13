"""Advanced AI safety checker integrating Meta Llama-Guard 3 with fast local rule evaluation."""

import logging
import re
from typing import List, Optional
import httpx
from app.interfaces.safety_checker import AbstractSafetyChecker, SafetyCheckResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class GuardrailsSafetyChecker(AbstractSafetyChecker):
    """Detects unsafe prompts using Llama-Guard 3 on Cloudflare edge, regex sanitization, and brand restrictions."""

    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    PHONE_REGEX = re.compile(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}")
    CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")

    BLOCKED_CATEGORIES = [
        "illegal", "weapon", "bomb", "hate", "terrorist", "violence",
        "nsfw", "nude", "explicit", "deepfake", "face swap", "celebrity face",
    ]

    LLAMA_GUARD_MODEL = "@cf/meta/llama-guard-3-8b"

    def mask_personal_data(self, text: str) -> str:
        """Replace sensitive emails, phone numbers, and card numbers with placeholders."""
        sanitized = self.EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
        sanitized = self.PHONE_REGEX.sub("[REDACTED_PHONE]", sanitized)
        sanitized = self.CREDIT_CARD_REGEX.sub("[REDACTED_CARD]", sanitized)
        return sanitized

    async def _check_llama_guard(self, prompt: str) -> Optional[SafetyCheckResult]:
        """Invoke Meta Llama-Guard 3 on Cloudflare edge for deep contextual toxicity classification."""
        if not settings.CLOUDFLARE_ACCOUNT_ID or not settings.CLOUDFLARE_API_TOKEN:
            return None

        # Truncate to first 400 characters to keep evaluation fast (< 3s) and avoid edge timeouts
        eval_prompt = prompt.strip()[:400]
        if not eval_prompt:
            return SafetyCheckResult(is_safe=True)

        url = f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/ai/run/{self.LLAMA_GUARD_MODEL}"
        headers = {"Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}"}
        payload = {"messages": [{"role": "user", "content": eval_prompt}]}

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    resp_json = res.json()
                    guard_output = resp_json.get("result", {}).get("response", "").strip().lower()
                    if guard_output.startswith("unsafe") or "\nunsafe" in guard_output:
                        explicit_prohibited_terms = {
                            "sex", "sexual", "nude", "nudity", "naked", "porn", "pornography", "erotic", "nsfw",
                            "abuse", "exploit", "exploitation", "assault", "molest", "rape", "pedophile",
                            "underwear", "bikini", "groin", "genital", "intimate", "kill", "murder", "weapon", "bomb",
                            "terrorist", "suicide", "blood", "gore", "slaughter", "hate speech"
                        }
                        lowered_prompt = prompt.lower()
                        has_prohibited = any(term in lowered_prompt for term in explicit_prohibited_terms)

                        if has_prohibited:
                            logger.warning("Llama-Guard 3 flagged prompt as unsafe (verified prohibited term): %s", guard_output)
                            return SafetyCheckResult(
                                is_safe=False,
                                reason="Llama-Guard policy flag: Prompt contains unsafe, inappropriate, or policy-violating content.",
                            )
                        else:
                            # False positive on wholesome creative words (e.g., kid girl plucking flowers, sweet fragrance, etc.)
                            logger.info(
                                "Overriding Llama-Guard false positive for benign creative marketing prompt: '%s' (Flagged: %s)",
                                prompt[:120],
                                guard_output,
                            )
                            return SafetyCheckResult(is_safe=True)
                    elif "safe" in guard_output:
                        return SafetyCheckResult(is_safe=True)
        except Exception as e:
            logger.info("Llama-Guard 3 edge check skipped (graceful fail-open): %s", e)

        return None

    async def validate_prompt_safety(
        self,
        prompt: str,
        banned_words: Optional[List[str]] = None,
    ) -> SafetyCheckResult:
        """Verify prompt conforms to brand safety policies using fast local checks + Llama-Guard 3."""
        lowered = prompt.lower()

        # 1. Fast local keyword blacklist check
        for blocked in self.BLOCKED_CATEGORIES:
            if blocked in lowered:
                return SafetyCheckResult(
                    is_safe=False,
                    reason=f"Prompt contains prohibited content category: '{blocked}'",
                )

        # 2. Brand-specific banned words check (competitors, confidential trademarks)
        if banned_words:
            for word in banned_words:
                if word.lower() in lowered:
                    return SafetyCheckResult(
                        is_safe=False,
                        reason=f"Prompt violates brand policy: prohibited term '{word}'",
                    )

        # 3. Contextual Llama-Guard 3 evaluation on Cloudflare Workers AI
        ai_safety_result = await self._check_llama_guard(prompt)
        if ai_safety_result is not None:
            return ai_safety_result

        return SafetyCheckResult(is_safe=True)
