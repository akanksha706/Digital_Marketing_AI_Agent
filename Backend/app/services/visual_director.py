"""Dynamic AI Art Direction, Spatial Layout Analysis & Cinematographic Prompt Synthesis Engine."""

import io
import json
import logging
import re
import httpx
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageFilter

from app.core.config import settings
from app.core.prompts import (
    build_poster_director_system_prompt,
    enhance_image_prompt,
    VIDEO_MOTION_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class VisualLayoutAnalyzer:
    """Calculates image safe spaces, luminance, and layout positioning."""

    @classmethod
    async def analyze_image_llm(
        cls,
        image_input: Image.Image | bytes,
        brand_primary: Optional[str] = None,
        brand_secondary: Optional[str] = None,
    ) -> dict:
        """Analyzes image layout and contrast using multimodal vision inference."""
        account_id = settings.CLOUDFLARE_ACCOUNT_ID
        token = settings.CLOUDFLARE_API_TOKEN

        try:
            if isinstance(image_input, bytes):
                img = Image.open(io.BytesIO(image_input)).convert("RGB")
            else:
                img = image_input.convert("RGB")

            if account_id and token:
                # Downsample to 512x512 for fast vision inference
                small = img.resize((512, 512), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                small.save(buf, format="JPEG", quality=85)
                img_bytes = list(buf.getvalue())

                prompt = (
                    "You are an expert AI Visual Layout Director for luxury brand posters and social video reels. "
                    "Analyze this image carefully and return a JSON object with:\n"
                    "1. 'objects': description of detected people, faces, eyes, hands, tables, trays, and their exact vertical position (e.g. 'woman face at y=20-45%, body at y=45-80%, tray at y=50-70%')\n"
                    "2. 'empty_space': description of where clean open negative space exists (e.g. 'upper 25% in sky well above head' or 'lower 20% in foreground water')\n"
                    "3. 'empty_space_tone': 'dark' or 'light'\n"
                    "4. 'recommended_y_percent': integer percentage (14 to 82) where the headline should be centered.\n"
                    "   CRITICAL FACE & SUBJECT AVOIDANCE RULES (MANDATORY):\n"
                    "   - Text must NEVER cover a person's face, forehead, eyes, head, hands, or held items/trays/offerings!\n"
                    "   - If open sky, ceiling, or generous headroom exists above the subject (y=0% to 35%), you MUST place headline in the upper open space (recommended_y_percent between 14 and 20), well clear above the hair/head.\n"
                    "   - If the upper half is occupied and clean open space is in the bottom foreground (y=78% to 88%) completely clear of hands and props, place headline at recommended_y_percent between 78 and 84.\n"
                    "   - NEVER choose y between 25 and 75 if a human head, face, hands, or held items are present there!\n"
                    "5. 'headline_color': hex color for headline (#FFFFFF or radiant gold #F5C042 for dark/night/dusk/golden hour, #0F172A for bright/white background)\n"
                    "6. 'quote_color': hex color for quote (#FEF08A or #FFF4D6 for dark/warm background, #334155 for bright background)\n"
                    "7. 'accent_color': hex color for divider (#F59E0B or #EAB308)\n"
                    "Respond ONLY with a valid JSON object."
                )

                url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/meta/llama-3.2-11b-vision-instruct"
                async with httpx.AsyncClient(timeout=35.0) as client:
                    res = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {token}"},
                        json={
                            "prompt": prompt,
                            "image": img_bytes,
                            "max_tokens": 512,
                        },
                    )
                    if res.status_code == 200:
                        raw = res.json().get("result", {}).get("response", "")
                        m = re.search(r"\{[\s\S]*\}", raw)
                        if m:
                            parsed = json.loads(m.group(0))
                            y_rec = int(parsed.get("recommended_y_percent", 16))
                            is_top = y_rec < 45
                            placement = "top" if is_top else "bottom"

                            # Dynamic vertical ratios: never arbitrary hardcoding
                            ui_y = max(14, min(82, y_rec))
                            headline_y_ratio = max(0.08, min(0.78, (ui_y - 6) / 100.0))
                            quote_y_ratio = max(0.16, min(0.88, (ui_y + 8) / 100.0))

                            if is_top:
                                crop_box = (int(img.width * 0.10), int(img.height * 0.04), int(img.width * 0.90), int(img.height * 0.32))
                            else:
                                crop_box = (int(img.width * 0.10), int(img.height * 0.70), int(img.width * 0.90), int(img.height * 0.94))

                            # Photometric color sampling from the exact selected zone
                            zone_crop = img.crop(crop_box)
                            zone_gray = np.array(zone_crop.convert("L"), dtype=np.float32)
                            mean_lum = float(np.mean(zone_gray))

                            zone_rgb = np.array(zone_crop.convert("RGB"), dtype=np.float32)
                            mean_r = float(np.mean(zone_rgb[:, :, 0]))

                            # Determine optimal high-contrast colors automatically
                            llm_h = parsed.get("headline_color")
                            llm_q = parsed.get("quote_color")
                            llm_acc = parsed.get("accent_color")

                            if mean_lum >= 175:
                                is_dark = False
                                h_color = llm_h if (llm_h and llm_h.lower() not in ["#ffffff", "#fff"]) else "#0F172A"
                                q_color = llm_q if (llm_q and llm_q.lower() not in ["#ffffff", "#fff", "#fef08a"]) else "#334155"
                                acc_color = llm_acc or ("#B45309" if mean_r > 150 else "#1D4ED8")
                            else:
                                is_dark = True
                                # On rich or warm morning dusk/dawn/night background, prefer radiant gold or crisp white
                                h_color = llm_h if (llm_h and llm_h.lower() != "#0f172a") else ("#F5C042" if mean_r > 100 else "#FFFFFF")
                                q_color = llm_q if (llm_q and llm_q.lower() != "#0f172a") else ("#FEF08A" if mean_lum < 110 else "#FFF4D6")
                                acc_color = llm_acc or "#F59E0B"

                            logger.info(
                                "LLM Vision Analysis succeeded: objects=%s, space=%s, placement=%s (y=%d), zone_lum=%.1f, h_color=%s",
                                parsed.get("objects"), parsed.get("empty_space"), placement, ui_y, mean_lum, h_color
                            )

                            return {
                                "placement": placement,
                                "headline_y_ratio": round(headline_y_ratio, 3),
                                "quote_y_ratio": round(quote_y_ratio, 3),
                                "x": 50,
                                "y": ui_y,
                                "scale": 1.0,
                                "width": 82,
                                "rotation": 0,
                                "gap": 14,
                                "zone_luminance": round(mean_lum, 1),
                                "headline_color": h_color,
                                "accent_color": acc_color,
                                "quote_color": q_color,
                                "is_dark_background": is_dark,
                                "badge_bg": "rgba(255, 255, 255, 0.95)" if is_dark else "rgba(15, 23, 42, 0.92)",
                                "badge_text": "#0F172A" if is_dark else "#FFFFFF",
                                "llm_vision_meta": parsed,
                            }
        except Exception as e:
            logger.warning("LLM Vision analysis failed or timed out: %s. Falling back to computational scan.", e)

        # Fallback to computational edge and luminance analysis
        return cls.analyze_image(image_input, brand_primary, brand_secondary)

    @classmethod
    def analyze_image(
        cls,
        image_input: Image.Image | bytes,
        brand_primary: Optional[str] = None,
        brand_secondary: Optional[str] = None,
        known_subject_bbox: Optional[Tuple[int, int, int, int]] = None,
    ) -> dict:
        """Calculates safe negative space placement, contrast color scheme, and layout metadata."""
        try:
            if isinstance(image_input, bytes):
                img = Image.open(io.BytesIO(image_input)).convert("RGB")
            else:
                img = image_input.convert("RGB")
        except Exception as e:
            logger.warning("VisualLayoutAnalyzer failed to open image: %s. Using safe defaults.", e)
            return cls._default_layout(brand_primary, brand_secondary)

        width, height = img.size
        is_vertical = height > width

        # -------------------------------------------------------------
        # 1. Determine Subject Position & Negative/Blank Space
        # -------------------------------------------------------------
        top_safe_score = 0.0
        bottom_safe_score = 0.0

        if known_subject_bbox:
            # known_subject_bbox is (pos_x, pos_y, subj_w, subj_h)
            pos_x, pos_y, subj_w, subj_h = known_subject_bbox
            subj_top = pos_y / float(height)
            subj_bottom = (pos_y + subj_h) / float(height)
            subj_center_y = (subj_top + subj_bottom) / 2.0

            # If subject sits in lower 65% of screen, TOP space is completely open
            if subj_center_y >= 0.45:
                top_safe_score = 10.0
            else:
                bottom_safe_score = 10.0
        else:
            # Computational Edge Density & Variance Analysis across vertical bands
            gray = img.convert("L")
            edges = gray.filter(ImageFilter.FIND_EDGES)
            edge_arr = np.array(edges, dtype=np.float32)
            gray_arr = np.array(gray, dtype=np.float32)

            num_bands = 10
            band_h = height // num_bands
            complexities = []
            luminances = []

            for i in range(num_bands):
                y0 = i * band_h
                y1 = (i + 1) * band_h
                b_edges = edge_arr[y0:y1, :]
                b_gray = gray_arr[y0:y1, :]
                c = float(np.mean(b_edges) + np.std(b_gray) * 0.4)
                lum = float(np.mean(b_gray))
                complexities.append(c)
                luminances.append(lum)

            # Top safe zone: bands 1-3 (10% to 35% height)
            # Bottom safe zone: bands 6-8 (65% to 88% height)
            top_comp = float(np.mean(complexities[1:4]))
            bottom_comp = float(np.mean(complexities[6:9]))

            # Lower complexity = cleaner negative space
            top_safe_score = 100.0 / (top_comp + 1e-4)
            bottom_safe_score = 100.0 / (bottom_comp + 1e-4)

        # Prefer whichever zone has lower complexity (cleaner empty space)
        # In portraits and landscape scenes, open sky / headroom is the premier location for typography
        if top_safe_score >= bottom_safe_score * 0.85:
            placement = "top"
            headline_y_ratio = 0.10
            quote_y_ratio = 0.20
            ui_y_percent = 15
            zone_y0 = int(height * 0.04)
            zone_y1 = int(height * 0.32)
        else:
            placement = "bottom"
            headline_y_ratio = 0.78
            quote_y_ratio = 0.86
            ui_y_percent = 80
            zone_y0 = int(height * 0.75)
            zone_y1 = int(height * 0.95)

        # -------------------------------------------------------------
        # 2. Photometric Color Analysis of the Chosen Negative Space
        # -------------------------------------------------------------
        zone_crop = img.crop((int(width * 0.15), zone_y0, int(width * 0.85), zone_y1))
        zone_gray = np.array(zone_crop.convert("L"), dtype=np.float32)
        mean_lum = float(np.mean(zone_gray))

        zone_rgb = np.array(zone_crop, dtype=np.float32)
        mean_r = float(np.mean(zone_rgb[:, :, 0]))
        mean_g = float(np.mean(zone_rgb[:, :, 1]))
        mean_b = float(np.mean(zone_rgb[:, :, 2]))

        # Golden temple lighting, warm chandeliers, and rich festive ambiance often register lum 130-175
        # but are rich colored scenes where dark slate text is completely unreadable.
        # Only true pale white/light grey studio backgrounds (mean_lum >= 195) should use dark text.
        is_pale_studio = mean_lum >= 195
        is_dark = not is_pale_studio

        if not is_pale_studio:
            # Luminous crisp white & radiant amber gold with chiaroscuro 3D drop shadow for crystal readability
            headline_color = "#FFFFFF"
            accent_color = "#F59E0B"  # Vibrant amber gold (high viral engagement)
            quote_color = "#FEF08A" if mean_lum < 95 else "#FFDF0F"
            badge_bg = "rgba(255, 255, 255, 0.95)"
            badge_text = "#0F172A"
        else:
            # Pure white daylight or pale minimalist studio backdrop
            headline_color = "#0F172A"  # Deep midnight slate
            accent_color = "#B45309" if mean_r > 155 else "#1D4ED8"
            quote_color = "#334155"  # Refined dark slate
            badge_bg = "rgba(15, 23, 42, 0.92)"
            badge_text = "#FFFFFF"

        # If brand secondary color provides strong contrast, incorporate brand harmony
        if brand_primary and brand_primary.startswith("#") and len(brand_primary) == 7:
            try:
                bp_r = int(brand_primary[1:3], 16)
                bp_g = int(brand_primary[3:5], 16)
                bp_b = int(brand_primary[5:7], 16)
                bp_lum = 0.299 * bp_r + 0.587 * bp_g + 0.114 * bp_b
                # If brand primary has good contrast against the zone luminance
                if abs(bp_lum - mean_lum) > 70:
                    accent_color = brand_primary
            except Exception:
                pass

        logger.info(
            "VisualLayoutAnalyzer: Detected safe zone '%s' (y=%s%%), lum=%.1f, is_dark=%s",
            placement, ui_y_percent, mean_lum, is_dark
        )

        return {
            "placement": placement,
            "headline_y_ratio": round(headline_y_ratio, 3),
            "quote_y_ratio": round(quote_y_ratio, 3),
            "x": 50,
            "y": ui_y_percent,
            "scale": 1.0,
            "width": 82,
            "rotation": 0,
            "gap": 14,
            "zone_luminance": round(mean_lum, 1),
            "headline_color": headline_color,
            "accent_color": accent_color,
            "quote_color": quote_color,
            "is_dark_background": is_dark,
            "badge_bg": badge_bg,
            "badge_text": badge_text,
        }

    @staticmethod
    def _default_layout(brand_primary: Optional[str] = None, brand_secondary: Optional[str] = None) -> dict:
        """Safe default fallback layout."""
        return {
            "placement": "top",
            "headline_y_ratio": 0.08,
            "quote_y_ratio": 0.15,
            "x": 50,
            "y": 12,
            "scale": 1.0,
            "width": 82,
            "rotation": 0,
            "gap": 14,
            "zone_luminance": 80.0,
            "headline_color": brand_secondary or "#FFFFFF",
            "accent_color": brand_primary or "#F59E0B",
            "quote_color": "#FFDF0F",
            "is_dark_background": True,
            "badge_bg": "rgba(255, 255, 255, 0.95)",
            "badge_text": "#0F172A",
        }


class VisualDirector:
    """Orchestrates dynamic visual art direction, cinematography guidelines, and social copywriting."""

    @classmethod
    def get_system_prompt(cls, brand_tone: str, banned_words: Optional[list[str]] = None) -> str:
        """Builds director system prompt for LLaMA 3.1."""
        return build_poster_director_system_prompt(brand_tone=brand_tone, banned_words=banned_words)

    @classmethod
    def finalize_image_prompt(cls, generated_prompt: str) -> str:
        """Applies photorealism anchors and safety rules to the visual prompt."""
        return enhance_image_prompt(generated_prompt)

    @classmethod
    async def synthesize_motion_prompt(
        cls,
        prompt: str,
        headline: str = "",
        quote: str = "",
        vision_context: Optional[str] = None,
    ) -> str:
        """Generates dynamic physical action brief for video diffusion."""
        account_id = settings.CLOUDFLARE_ACCOUNT_ID
        token = settings.CLOUDFLARE_API_TOKEN

        subject = prompt.strip() if prompt else headline.strip()
        fallback_prompt = (
            f"{subject}. Authentic cinematic human motion, natural gestures, lifelike eye contact, "
            f"subtle facial expressions, living environmental physics, smooth camera push-in, photorealistic 8k"
        )

        if not account_id or not token:
            return fallback_prompt

        # Retrieve live real-world visual context if not already provided
        if not vision_context:
            try:
                from app.services.visual_knowledge_service import VisualKnowledgeService
                vision_context = await VisualKnowledgeService.retrieve_visual_knowledge(subject)
            except Exception:
                pass

        system_instruction = VIDEO_MOTION_SYSTEM_PROMPT

        visual_cue = f"Visual Image Context: {vision_context}\n" if vision_context else ""
        user_content = (
            f"{visual_cue}Subject/Prompt: {prompt}\n"
            f"Headline: {headline}\n"
            f"Story Quote: {quote}\n\n"
            f"Describe the realistic physical action and camera motion for this video reel:"
        )

        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/meta/llama-3.1-8b-instruct"
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_content},
                        ],
                        "max_tokens": 128,
                    },
                )
                if res.status_code == 200:
                    raw = res.json().get("result", {}).get("response", "").strip()
                    cleaned = re.sub(r"^[\"'\`]+|[\"'\`]+$", "", raw).strip()
                    if cleaned and len(cleaned) > 20:
                        logger.info("LLM Brain synthesized video motion prompt: %s", cleaned)
                        return cleaned
        except Exception as err:
            logger.warning("LLM Brain motion prompt synthesis fallback: %s", err)

        return fallback_prompt

