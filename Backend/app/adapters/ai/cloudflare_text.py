"""Cloudflare Workers AI implementation for storytelling copy and visual composition."""

import re
import json
import logging
from typing import List, Optional
import httpx
from app.interfaces.text_generator import AbstractTextGenerator, PosterPlan
from app.core.config import settings
from app.services.visual_director import VisualDirector
from app.services.visual_knowledge_service import VisualKnowledgeService
from app.core.prompts import build_poster_user_prompt

logger = logging.getLogger(__name__)


def sanitize_cjk_characters(text: Optional[str]) -> str:
    """Strips any hallucinated East Asian characters (Chinese Hanzi, Japanese Kanji/Kana, Korean Hangul)."""
    if not text:
        return ""
    # CJK Unified Ideographs, Hiragana, Katakana, CJK Ext A, Hangul, Fullwidth Forms
    cjk_pattern = r"[\u4e00-\u9fff\u3040-\u30ff\u3400-\u4dbf\uac00-\ud7af\uff00-\uffef]+"
    cleaned = re.sub(cjk_pattern, "", text)
    return re.sub(r" +", " ", cleaned).strip()


class CloudflareTextGenerator(AbstractTextGenerator):
    """Generates storytelling copy and cinematic visual plans using Llama 3.1 8B."""

    def __init__(self):
        self.account_id = settings.CLOUDFLARE_ACCOUNT_ID
        self.api_token = settings.CLOUDFLARE_API_TOKEN
        self.model = settings.TEXT_MODEL
        self.endpoint = (
            f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"
        )

    def _build_system_prompt(self, brand_tone: str, banned_words: Optional[List[str]] = None) -> str:
        """Construct system instructions enforcing poetic storytelling and cinematic composition."""
        return VisualDirector.get_system_prompt(brand_tone=brand_tone, banned_words=banned_words)

    async def generate_poster_plan(
        self,
        prompt: str,
        brand_tone: str,
        banned_words: Optional[List[str]] = None,
    ) -> PosterPlan:
        """Invoke Llama 3.1 model to generate storytelling copy and design layout plan."""
        # Use development fallback stub if API token is not yet configured
        if not self.api_token or not self.account_id:
            logger.info("Cloudflare credentials not provided. Using intelligent local mock.")
            topic = prompt.strip()
            return PosterPlan(
                headline="Where Shadows Fade, Light Begins",
                story_quote="One humble flame can conquer a thousand shadows. This festive season, let your courage illuminate the world.",
                sub_tagline=f"{topic.upper()}  •  2026",
                caption=(
                    f"As we celebrate {topic}, we reflect on the timeless triumph of hope over despair. ✨\n\n"
                    "Wonderful Thoughts for a Brighter Path:\n"
                    "• Let Go of the Old: Welcome new opportunities with open arms.\n"
                    "• Choose Positivity: A bright mind lights every corridor.\n"
                    "• Spread Kindness: True radiance is in the lives we touch.\n\n"
                    "Wishing you peace, prosperity, and joy on this special occasion!"
                ),
                hashtags=[f"#{topic.replace(' ', '')}", "#FestivalOfLights", "#Inspiration", "#Celebration"],
                quote="One humble flame can conquer a thousand shadows.",
                image_prompt="Cinematic storytelling scene of a glowing traditional earthen diya on reflective wet slate floor, warm golden flame casting rays into atmospheric twilight, deep natural dark shadows in lower third for seamless typography, 8k commercial photography, no text",
                template_name="cinematic_story",
            )

        # Step 0: Live Web Visual Knowledge Grounding (prevents festival hallucination & repetition)
        web_knowledge = ""
        try:
            web_knowledge = await VisualKnowledgeService.retrieve_visual_knowledge(prompt)
        except Exception as k_err:
            logger.warning("Knowledge retrieval fallback: %s", k_err)

        user_content = build_poster_user_prompt(prompt)
        if web_knowledge:
            user_content = (
                f"{user_content}\n\n"
                f"=== LIVE RETRIEVED REAL-WORLD KNOWLEDGE & VISUAL FACTS ===\n"
                f"{web_knowledge}\n"
                f"STRICT INSTRUCTION: Ground your visual setting, human actions, colors, and subject matter "
                f"strictly in the verified real-world facts above. Never fall back to generic festival or living room "
                f"tropes unless explicitly requested by the user."
            )

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messages": [
                {"role": "system", "content": self._build_system_prompt(brand_tone, banned_words)},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": 1000,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                raw_content = data.get("result", {}).get("response", "{}")

                if isinstance(raw_content, dict):
                    parsed = raw_content
                else:
                    raw_str = str(raw_content).strip()
                    if raw_str.startswith("```json"):
                        raw_str = raw_str[7:]
                    if raw_str.startswith("```"):
                        raw_str = raw_str[3:]
                    if raw_str.endswith("```"):
                        raw_str = raw_str[:-3]

                    raw_str = raw_str.strip()
                    # Clean invalid JSON escapes like \' that LLMs sometimes generate
                    raw_str = re.sub(r"\\'", "'", raw_str)

                    try:
                        parsed = json.loads(raw_str, strict=False)
                    except json.JSONDecodeError:
                        # Fix unescaped raw newlines in JSON strings without destroying formatting
                        fixed = re.sub(r'(?<!\\)\r?\n', r'\\n', raw_str)
                        try:
                            parsed = json.loads(fixed, strict=False)
                        except json.JSONDecodeError:
                            cleaned = re.sub(r'[\r\n\t]+', ' ', raw_str)
                            parsed = json.loads(cleaned, strict=False)

                if isinstance(parsed, dict):
                    # Normalize any LLM key variations for quote
                    for k in ["reflection", "thought", "quote", "tagline", "subquote"]:
                        if k in parsed and not parsed.get("story_quote"):
                            parsed["story_quote"] = parsed[k]

                    # Sanitize any hallucinated Chinese/Japanese/Korean characters across all fields
                    for field in ["headline", "sub_tagline", "story_quote", "quote", "caption", "image_prompt"]:
                        if field in parsed and isinstance(parsed[field], str):
                            parsed[field] = sanitize_cjk_characters(parsed[field])

                    if "hashtags" in parsed and isinstance(parsed["hashtags"], list):
                        parsed["hashtags"] = [sanitize_cjk_characters(tag) for tag in parsed["hashtags"] if sanitize_cjk_characters(tag)]

                    # Clean any prompt command echo from headline
                    if "headline" in parsed and isinstance(parsed["headline"], str):
                        cleaned_hl = re.sub(
                            r"^(create\s+(an?\s+)?(elegant\s+|celebration\s+|social\s+)?(poster|video|reel)\s+(for\s+)?(the\s+)?)",
                            "",
                            parsed["headline"],
                            flags=re.I,
                        ).strip()
                        if cleaned_hl:
                            parsed["headline"] = cleaned_hl

                    plan = PosterPlan(**parsed)
                else:
                    plan = PosterPlan(**parsed)

                # Ensure final photorealistic anchors and anti-text constraints without keyword bloat or hardcoded bluff
                plan.image_prompt = VisualDirector.finalize_image_prompt(plan.image_prompt)
                return plan
        except Exception as exc:
            logger.warning("Cloudflare text generation rate-limited or unavailable (%s). Using adaptive fallback plan.", exc)
            lower_p = prompt.lower()
            if "gurudwara" in lower_p or "god" in lower_p or "temple" in lower_p or "divine" in lower_p:
                headline = "Divine Radiance"
                sub_tagline = "SACRED DARBAR • 2026"
            elif "cycle" in lower_p or "riding" in lower_p:
                headline = "Pedaling Dreams Forward"
                sub_tagline = "ADVENTURE • 2026"
            elif "christmas" in lower_p or "santa" in lower_p:
                headline = "Festive Warmth & Joy"
                sub_tagline = "SEASON'S GREETINGS • 2026"
            elif "fish" in lower_p or "water" in lower_p:
                headline = "Ripples of Wonder"
                sub_tagline = "OCEAN DISCOVERY • 2026"
            else:
                clean_title = re.sub(r"^(social media campaign|campaign|make this person in the image|make this person|make|create|generate|highlight|show|put|seat)\s*:?\s*", "", prompt, flags=re.I).strip()
                words = [w for w in clean_title.split() if w.lower() not in ["this", "person", "image", "the", "like", "a", "at", "in", "with"]][:3]
                headline = " ".join(words).title() if words else "Inspiring Excellence"
                sub_tagline = "FEATURED SPOTLIGHT • 2026"
            return PosterPlan(
                headline=headline,
                story_quote="In the sacred stillness, we discover the peace and divine light that illuminates our souls.",
                sub_tagline=sub_tagline,
                caption=(
                    f"Reflecting on {headline}. ✨\n\n"
                    "Guiding Principles for Life and Growth:\n"
                    "• Inner Stillness: Peace begins within the quiet heart.\n"
                    "• Selfless Service: The highest virtue is devotion and kindness.\n"
                    "• Timeless Wisdom: Let wisdom light the path through all challenges.\n\n"
                    "Wishing you peace, harmony, and joy!"
                ),
                hashtags=["#DivineSerenity", "#SpiritualJourney", "#FaithAndPeace", "#Inspiration"],
                quote="In the stillness of the heart, we find the silence that speaks to our souls.",
                image_prompt=prompt,
                template_name="cinematic_story",
            )
