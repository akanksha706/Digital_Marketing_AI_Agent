"""Interface for content moderation and PII masking."""

from abc import ABC, abstractmethod
from pydantic import BaseModel


class SafetyCheckResult(BaseModel):
    """Result of content safety inspection."""
    is_safe: bool
    reason: str = ""


class AbstractSafetyChecker(ABC):
    """Abstract contract for safety and privacy guardrails."""

    @abstractmethod
    def mask_personal_data(self, text: str) -> str:
        """Sanitize personal data (emails, phone numbers) before sending to AI models."""
        pass

    @abstractmethod
    async def validate_prompt_safety(self, prompt: str) -> SafetyCheckResult:
        """Check if user prompt complies with brand and content safety standards."""
        pass
