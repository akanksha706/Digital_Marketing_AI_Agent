"""Custom user image upload service integrating Llama-Guard 3 safety checks with creative poster generation."""

import base64
import io
import json
import logging
import math
import random
import re
import uuid
from pathlib import Path
from typing import Optional
import httpx
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.safety.guardrails import GuardrailsSafetyChecker
from app.adapters.ai.cloudflare_image import CloudflareImageGenerator
from app.core.config import settings
from app.db.models import Poster, Brand, PostStatus, User
from app.interfaces.image_generator import AbstractImageGenerator
from app.interfaces.storage_provider import AbstractStorageProvider
from app.interfaces.text_generator import AbstractTextGenerator
from app.services.poster_compositor import PosterCompositor
from app.services.visual_director import VisualLayoutAnalyzer
from app.services.visual_director import VisualDirector

logger = logging.getLogger(__name__)


async def _ai_dynamic_edit(img: Image.Image, prompt: str, filename: Optional[str] = None) -> Image.Image:
    """Master AI Visual Director & Foundation Synthesis:
    Preserves 100% exact face, facial expression, and body shape of the uploaded person/subject
    when placing them in new environments (thrones, temples, gurudwaras, offices, landscapes),
    and creates cohesive organic action scenes for cartoon/brand assets.
    """
    account_id = settings.CLOUDFLARE_ACCOUNT_ID
    token = settings.CLOUDFLARE_API_TOKEN

    orig_rgb = img.convert("RGB")
    w_orig, h_orig = orig_rgb.size
    prompt_lower = prompt.lower().strip()

    # Determine if request is a placement / environment / setting change
    environment_keywords = [
        "seat", "sit", "sitting", "center", "centre", "gurudwara", "temple", "church", "mosque",
        "office", "beach", "background", "throne", "stage", "place", "put", "hall", "room",
        "palace", "garden", "mountain", "surrounded", "setting", "environment", "stand in", "at center"
    ]
    is_environment_placement = any(k in prompt_lower for k in environment_keywords)

    # Attempt subject extraction to preserve exact face and body
    extracted_subj = None
    try:
        from rembg import remove, new_session
        session = new_session("u2netp")
        alpha_img = remove(orig_rgb, session=session)
        # Check if subject extraction yielded a valid cutout
        alpha_channel = alpha_img.split()[3]
        alpha_np = np.array(alpha_channel)
        coverage = np.sum(alpha_np > 30) / alpha_np.size
        if 0.08 <= coverage <= 0.92:
            extracted_subj = alpha_img
            logger.info("Successfully extracted subject with exact face/body (coverage=%.2f)", coverage)
    except Exception as e:
        logger.warning("Subject extraction for exact face preservation skipped: %s", e)

    # ---------------------------------------------------------
    # MODE 1: Exact Face & Body Preservation in New Environment
    # ---------------------------------------------------------
    if is_environment_placement and extracted_subj is not None:
        logger.info("Preserving EXACT face and body for environment prompt: %s", prompt[:80])
        w_t, h_t = (1024, 1024)

        # Generate clean empty environment background
        bg_prompt = (
            f"{prompt}, wide angle architectural view, magnificent lighting, 8k resolution, "
            "empty center, empty throne, sacred hall, devotional fine art, no people, no person, empty"
        )
        bg_image: Optional[Image.Image] = None

        # Try Cloudflare FLUX first
        if account_id and token:
            try:
                url_flux = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
                async with httpx.AsyncClient(timeout=40.0) as client:
                    f_res = await client.post(
                        url_flux,
                        headers={"Authorization": f"Bearer {token}"},
                        json={"prompt": bg_prompt},
                    )
                    if f_res.status_code == 200 and len(f_res.content) > 100:
                        raw_b = f_res.content
                        if f_res.content.startswith(b"{"):
                            b64 = f_res.json().get("result", {}).get("image", "")
                            if b64:
                                raw_b = base64.b64decode(b64)
                        bg_image = Image.open(io.BytesIO(raw_b)).convert("RGB").resize((w_t, h_t))
                        logger.info("Generated environment background via Cloudflare FLUX")
            except Exception as e:
                logger.warning("Cloudflare FLUX bg generation failed: %s", e)

        # Fallback to high-resolution environment generation
        if bg_image is None:
            try:
                import urllib.parse
                clean_env_query = re.sub(r"(make this person|in the image|seat like a god|with proper body shape matching)", "", prompt, flags=re.I).strip()
                poll_prompt = f"majestic {clean_env_query} interior golden hall sacred darbar empty throne no people"
                encoded = urllib.parse.quote(poll_prompt[:120])
                url_poll = f"https://image.pollinations.ai/prompt/{encoded}?nologo=true"
                async with httpx.AsyncClient(timeout=35.0) as client:
                    p_res = await client.get(url_poll)
                    if p_res.status_code == 200 and len(p_res.content) > 1000:
                        raw_bg = Image.open(io.BytesIO(p_res.content)).convert("RGB")
                        # Crop bottom 5% watermark if present
                        bg_image = raw_bg.crop((0, 0, raw_bg.width, int(raw_bg.height * 0.95))).resize((w_t, h_t), Image.Resampling.LANCZOS)
                        logger.info("Generated environment background via fallback provider")
            except Exception as pe:
                logger.warning("Fallback environment generation failed: %s", pe)

        if bg_image is not None:
            # 1. Optical depth-of-field blur on background so subject pops cleanly
            bg_dof = bg_image.filter(ImageFilter.GaussianBlur(radius=2.5))

            # 2. Crop bottom 6% to strip any source watermarks from user upload
            w_s, h_s = extracted_subj.size
            subj_clean = extracted_subj.crop((0, 0, w_s, int(h_s * 0.94)))
            
            # 3. Scale subject to sit prominently and naturally grounded in lower half
            target_h = int(h_t * 0.65)
            target_w = int(subj_clean.width * (target_h / subj_clean.height))
            subj_resized = subj_clean.resize((target_w, target_h), Image.Resampling.LANCZOS)

            pos_x = (w_t - target_w) // 2
            pos_y = h_t - target_h - 35  # Firmly anchored to ground plane

            # 4. Multi-layer realistic contact & ambient occlusion shadows
            shadow_canvas = Image.new("RGBA", (w_t, h_t), (0, 0, 0, 0))
            s_draw = ImageDraw.Draw(shadow_canvas)
            base_y = pos_y + target_h
            # Layer 1: Tight dark contact shadow (AO) under base/feet
            s_draw.ellipse(
                [pos_x + 35, base_y - 12, pos_x + target_w - 35, base_y + 16],
                fill=(12, 8, 5, 230),
            )
            # Layer 2: Soft diffuse ground-spread shadow
            s_draw.ellipse(
                [pos_x + 10, base_y - 25, pos_x + target_w + 10, base_y + 45],
                fill=(18, 12, 8, 140),
            )
            shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(radius=15))

            # 5. Golden aura / divine halo if sacred/celebratory or ambient rim lighting
            is_divine = any(w in prompt_lower for w in ["god", "gurudwara", "temple", "divine", "throne", "sacred", "blessing", "light", "guru"])
            aura_canvas = Image.new("RGBA", (w_t, h_t), (0, 0, 0, 0))
            if is_divine:
                alpha = subj_resized.split()[3]
                halo = alpha.filter(ImageFilter.GaussianBlur(radius=28))
                aura_layer = Image.new("RGBA", (target_w, target_h), (255, 215, 80, 180))
                aura_canvas.paste(aura_layer, (pos_x, pos_y), mask=halo)

            # 6. Composite: Environment Background (with DOF) -> Shadow -> Aura -> Exact Subject
            final_composite = bg_dof.convert("RGBA")
            final_composite = Image.alpha_composite(final_composite, shadow_canvas)
            if is_divine:
                final_composite = Image.alpha_composite(final_composite, aura_canvas)
            final_composite.paste(subj_resized, (pos_x, pos_y), subj_resized)

            logger.info("Successfully composited EXACT subject with 100% original face, body, and ground contact into environment.")
            return final_composite.convert("RGB")

    # ---------------------------------------------------------
    # MODE 2: Action / Pose / Visual Synthesis via Foundation AI
    # ---------------------------------------------------------
    img_512 = orig_rgb.resize((512, 512), Image.Resampling.LANCZOS)
    buf_v = io.BytesIO()
    img_512.save(buf_v, format="JPEG", quality=85)

    # LLaVA 1.5 visual inspection
    subject_desc = ""
    if account_id and token:
        try:
            url_llava = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/llava-hf/llava-1.5-7b-hf"
            v_prompt = (
                "Identify the subject in this image in 2 sentences: "
                "character or subject name, art style (2D cartoon, anime, 3D animated Pixar, or real photo), "
                "distinctive physical features (colors, markings, clothing), and background."
            )
            async with httpx.AsyncClient(timeout=25.0) as client:
                v_res = await client.post(
                    url_llava,
                    headers={"Authorization": f"Bearer {token}"},
                    json={"image": list(buf_v.getvalue()), "prompt": v_prompt},
                )
                if v_res.status_code == 200:
                    subject_desc = v_res.json().get("result", {}).get("description", "").strip()
                    logger.info("LLaVA visual inspection: %s", subject_desc[:120])
        except Exception as e:
            logger.warning("LLaVA inspection error: %s", e)

    # Clean filename hint
    file_hint = ""
    if filename:
        clean_name = re.sub(r"[_\-\.]+", " ", Path(filename).stem).strip()
        file_hint = f"Asset filename hint: {clean_name}"

    # LLaMA 3.1 synthesizes cohesive master prompt
    master_prompt = ""
    if account_id and token:
        try:
            url_llama = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/meta/llama-3.1-8b-instruct"
            sys_prompt = (
                "You are an expert AI Visual Director crafting diffusion prompts for FLUX.1 image generation.\n"
                "Your task: Given an uploaded image description, filename hint, and user edit instruction, generate a single prompt that produces a cohesive, stunning visual while strictly preserving the EXACT identity, facial features, body shape, and ART STYLE of the subject.\n\n"
                "CRITICAL RULES:\n"
                "1. SUBJECT IDENTITY & ART STYLE MATCHING (MANDATORY):\n"
                "   - If the subject is a 2D cartoon / anime (e.g. Doraemon, Chhota Bheem, anime character, 2D comic):\n"
                "     * You MUST specify: 'classic 2D cel animation, clean crisp black vector line art, flat solid vibrant colors, authentic [show name / character style] art style'.\n"
                "     * Maintain their exact canonical features (e.g. red forehead tilak, ponytail tuft, yellow/red dhoti, gold armlets for Bheem; round blue robotic cat, red nose, whiskers, red collar with yellow bell, white pocket for Doraemon).\n"
                "     * Keep the background matching the original (e.g. textured warm yellow background for Doraemon, Indian village for Bheem).\n"
                "     * NEVER use '3D', 'Pixar', 'photorealistic', 'cinematic lighting', or 'hyperrealistic' for 2D characters! End with: ', authentic 2D cartoon animation, clean line art, no 3d render, no text'.\n"
                "   - If the subject is a 3D animated character (e.g. 3D animated goldfish, Pixar style):\n"
                "     * Specify: 'high quality 3D animated Disney Pixar style, vibrant lighting, smooth textures, [character details and action], award winning 3D animation, no text'.\n"
                "   - If the subject is a real human, real product, or photograph:\n"
                "     * Specify: 'professional commercial photography, studio lighting, sharp focus, 8k resolution, award-winning commercial photo, no text'.\n\n"
                "2. ACTION & POSE INTEGRATION:\n"
                "   - If the user asks for an action (e.g. riding a cycle, swimming, running):\n"
                "     * Depict the character organically performing the action (e.g. hands gripping handlebars, feet on pedals, natural riding posture).\n"
                "   - If the user asks for costumes or accessories (e.g. wear Christmas costume, Santa hat and scarf, sunglasses):\n"
                "     * Depict the character wearing those exact festive items naturally on their body/head while keeping their exact facial expression and body shape intact.\n\n"
                "3. NO COLLAGES, NO CUTOUTS, NO GHOSTS:\n"
                "   - The entire scene, character, and action must be synthesized as a single unified, appreciative masterpiece.\n\n"
                "Output ONLY the prompt text, with no explanations, no quotes, and no intro."
            )
            user_content = f"{file_hint}\nVisual Subject Reference: {subject_desc or 'uploaded character'}\nUser Edit Instruction: {prompt}"
            async with httpx.AsyncClient(timeout=15.0) as client:
                l_res = await client.post(
                    url_llama,
                    headers={"Authorization": f"Bearer {token}"},
                    json={"messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_content}]},
                )
                if l_res.status_code == 200:
                    raw_l = l_res.json().get("result", {}).get("response", "")
                    if isinstance(raw_l, str):
                        master_prompt = raw_l.strip().strip('"')
                    elif isinstance(raw_l, dict):
                        master_prompt = raw_l.get("response", "")
                    logger.info("Synthesized master prompt for '%s': %s", prompt[:60], master_prompt[:120])
        except Exception as e:
            logger.warning("LLaMA prompt synthesis error: %s", e)

    if not master_prompt:
        master_prompt = f"{prompt}, subject matching {subject_desc[:80]}, high quality artwork, no text"

    # FLUX.1 Schnell generates the complete unified masterpiece
    if account_id and token:
        url_flux = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                f_res = await client.post(
                    url_flux,
                    headers={"Authorization": f"Bearer {token}"},
                    json={"prompt": master_prompt},
                )
                if f_res.status_code == 200 and len(f_res.content) > 100:
                    raw_bytes = f_res.content
                    if "application/json" in f_res.headers.get("content-type", "") or f_res.content.startswith(b"{"):
                        data = f_res.json()
                        b64_image = data.get("result", {}).get("image", "")
                        if b64_image:
                            raw_bytes = base64.b64decode(b64_image)
                    generated_img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                    logger.info("Successfully synthesized unified appreciative masterpiece (%s bytes)", len(raw_bytes))
                    return generated_img
                else:
                    logger.warning("FLUX call returned code %s: %s", f_res.status_code, f_res.text[:120])
        except Exception as e:
            logger.warning("FLUX generation failed: %s", e)

    return orig_rgb


class CustomImageService:
    """Handles custom user uploaded images (person, product, award) and composites branded marketing posters."""

    def __init__(
        self,
        safety_checker: GuardrailsSafetyChecker,
        text_generator: AbstractTextGenerator,
        storage_provider: AbstractStorageProvider,
        image_generator: Optional[AbstractImageGenerator] = None,
        compositor: Optional[PosterCompositor] = None,
    ):
        self.safety_checker = safety_checker
        self.text_generator = text_generator
        self.storage_provider = storage_provider
        self.image_generator = image_generator or CloudflareImageGenerator()
        self.compositor = compositor or PosterCompositor()

    async def generate_from_uploaded_image(
        self,
        image_bytes: bytes,
        prompt: str,
        brand: Brand,
        aspect_ratio: str = "1:1",
        db: Optional[AsyncSession] = None,
        creator_id: Optional[int] = None,
        filename: Optional[str] = None,
    ) -> Poster:
        """Evaluates prompt with Llama-Guard 3, processes uploaded image, generates copy, and creates poster."""
        # 1. Llama-Guard 3 Safety Evaluation
        safety_res = await self.safety_checker.validate_prompt_safety(
            prompt=prompt,
            banned_words=brand.banned_words,
        )
        if not safety_res.is_safe:
            raise ValueError(f"Content Moderation Warning: {safety_res.reason}")

        # 2. Process and save uploaded image
        try:
            uploaded_img = Image.open(io.BytesIO(image_bytes))
            uploaded_img = ImageOps.exif_transpose(uploaded_img)
        except Exception as e:
            raise ValueError(f"Invalid image format provided: {str(e)}")

        file_id = uuid.uuid4().hex[:12]
        raw_storage_dir = Path(settings.LOCAL_STORAGE_DIR) / "posters"
        raw_storage_dir.mkdir(parents=True, exist_ok=True)
        raw_filename = f"{file_id}_user_upload.png"
        raw_filepath = raw_storage_dir / raw_filename

        uploaded_img.save(raw_filepath, format="PNG")
        user_asset_url = f"/static/posters/{raw_filename}"

        # 3. Determine whether user requested visual modifications or wants raw image unchanged
        prompt_lower = prompt.lower().strip()
        is_default_or_empty = prompt_lower in [
            "highlight and celebrate this featured visual asset in an elegant marketing poster",
            "",
        ]
        explicit_no_edit_request = any(
            phrase in prompt_lower
            for phrase in [
                "keep original image as is",
                "do not edit image",
                "no visual changes",
                "keep image as is",
                "leave photo as is",
                "use exact image without edit",
            ]
        )
        should_apply_ai_edit = not is_default_or_empty and not explicit_no_edit_request

        logger.info("Upload processing mode: should_apply_ai_edit=%s for prompt='%s'", should_apply_ai_edit, prompt[:60])

        # 4. Generate storytelling copy and plan using LLaMA 3.1
        augmented_prompt = (
            f"Social media campaign: {prompt}. "
            "Highlight the core theme with an inspiring headline, quote, and rich social media caption."
        )
        plan = await self.text_generator.generate_poster_plan(
            prompt=augmented_prompt,
            brand_tone=brand.tone_of_voice or "Celebratory & Professional",
            banned_words=brand.banned_words,
        )

        w, h = (1024, 1024) if aspect_ratio == "1:1" else (1024, 1280)

        # 5. Render or prepare background canvas
        if should_apply_ai_edit:
            # Dynamically execute user requested visual modifications via AI models (LLaVA 1.5 Vision + LLaMA 3.1 + FLUX.1 Schnell)
            logger.info("Executing AI Vision-conditioned FLUX synthesis for user prompt: %s (filename=%s)", prompt[:80], filename)
            active_img = await _ai_dynamic_edit(uploaded_img, prompt, filename=filename)
            fitted = ImageOps.fit(active_img.convert("RGB"), (w, h), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            fitted.save(buf, format="PNG")
            background_bytes = buf.getvalue()
        else:
            logger.info("Preserving exact original uploaded image without AI edits.")
            fitted = ImageOps.fit(uploaded_img.convert("RGB"), (w, h), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            fitted.save(buf, format="PNG")
            background_bytes = buf.getvalue()

        # Resolve standard brand logo (ensure uploaded user image is NEVER used as the logo emblem)
        composite_logo_bytes = None
        for candidate_logo in [
            Path("Backend/storage/brand/42Works_logo2.png"),
            Path("storage/brand/42Works_logo2.png"),
            Path("Frontend/public/42Works_logo2.png"),
            Path("Backend/storage/brand/42works_logo.png"),
            Path("storage/brand/42works_logo.png"),
        ]:
            if candidate_logo.exists():
                try:
                    composite_logo_bytes = candidate_logo.read_bytes()
                    break
                except Exception:
                    pass

        # 6. Save background scene and composite typography
        bg_filename = f"{file_id}_background.png"
        bg_filepath = raw_storage_dir / bg_filename
        bg_filepath.write_bytes(background_bytes)
        bg_url = f"/static/posters/{bg_filename}"

        final_filename = f"{file_id}_final.png"
        final_filepath = raw_storage_dir / final_filename

        # Autonomously scan visual negative space and harmonious colors
        layout_meta = VisualLayoutAnalyzer.analyze_image(
            image_input=background_bytes,
            brand_primary=brand.primary_color,
            brand_secondary=brand.secondary_color,
        )
        layout_meta["image_prompt"] = plan.image_prompt
        layout_meta["video_motion_prompt"] = plan.video_motion_prompt

        final_bytes = self.compositor.composite_poster(
            background_bytes=background_bytes,
            plan=plan,
            primary_color=layout_meta.get("accent_color", brand.primary_color or "#DFB876"),
            secondary_color=layout_meta.get("headline_color", brand.secondary_color or "#FDFBF7"),
            quote_color=layout_meta.get("quote_color"),
            headline_y_ratio=layout_meta.get("headline_y_ratio"),
            quote_y_ratio=layout_meta.get("quote_y_ratio"),
            logo_bytes=composite_logo_bytes,
        )
        final_filepath.write_bytes(final_bytes)
        final_url = f"/static/posters/{final_filename}"

        # 7. Persist Poster in PostgreSQL database with autonomous layout metadata
        valid_creator_id = creator_id
        if db and not valid_creator_id:
            first_user = (await db.execute(select(User).limit(1))).scalars().first()
            if first_user:
                valid_creator_id = first_user.id

        poster = Poster(
            brand_id=brand.id,
            created_by_id=valid_creator_id,
            prompt=prompt,
            headline=plan.headline,
            caption=plan.caption,
            hashtags=plan.hashtags,
            quote=plan.quote or plan.story_quote,
            background_image_url=bg_url,
            final_poster_url=final_url,
            template_name=plan.template_name,
            aspect_ratio=aspect_ratio,
            layout_meta=layout_meta,
            status=PostStatus.DRAFT,
        )

        if db:
            db.add(poster)
            await db.flush()
            await db.refresh(poster)

        return poster
