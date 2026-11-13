"""Cloudflare Workers AI implementation for background image generation."""

import base64
import io
import json
import logging
import re
import urllib.parse
import httpx
from PIL import Image, ImageDraw
from app.interfaces.image_generator import AbstractImageGenerator
from app.core.config import settings
from app.core.prompts import enhance_image_prompt

logger = logging.getLogger(__name__)


class CloudflareImageGenerator(AbstractImageGenerator):
    """Generates poster backgrounds using FLUX.1 schnell on Cloudflare Workers AI."""

    def __init__(self):
        self.account_id = settings.CLOUDFLARE_ACCOUNT_ID
        self.api_token = settings.CLOUDFLARE_API_TOKEN
        self.model = settings.IMAGE_MODEL
        self.endpoint = (
            f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"
        )

    def _generate_fallback_canvas(self, width: int = 1024, height: int = 1024) -> bytes:
        """Create a professional radial gradient canvas when API credentials are unset."""
        image = Image.new("RGB", (width, height), color="#1e1b4b")
        draw = ImageDraw.Draw(image)

        # Draw soft concentric decorative circles for atmospheric visual depth
        center_x, center_y = width // 2, height // 2
        colors = ["#312e81", "#3730a3", "#4338ca", "#4f46e5", "#6366f1"]
        for i, color in enumerate(colors):
            radius = (len(colors) - i) * 120
            draw.ellipse(
                [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                outline=color,
                width=3,
            )

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    async def generate_background(
        self,
        image_prompt: str,
        width: int = 1024,
        height: int = 1024,
    ) -> bytes:
        """Invoke FLUX.1 schnell to render clean background scene without text."""
        # Use development fallback canvas if credentials are unset
        if not self.api_token or not self.account_id:
            logger.info("Cloudflare credentials not provided. Using generated background canvas.")
            return self._generate_fallback_canvas(width, height)

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        # Guarantee no text in the prompt and command epic cinematic lighting
        refined_prompt = enhance_image_prompt(image_prompt)
        # Cloudflare Flux.1 Schnell enforces strict <= 2048 character limit
        if len(refined_prompt) > 1900:
            refined_prompt = refined_prompt[:1900].rsplit(" ", 1)[0].strip()

        payload = {
            "prompt": refined_prompt,
            "steps": 8,  # Higher fidelity step count for sharp details
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()

                raw_bytes = response.content
                # Cloudflare Workers AI returns a JSON wrapper containing base64 encoded image
                if "application/json" in response.headers.get("content-type", "") or response.content.startswith(b"{"):
                    data = response.json()
                    b64_image = data.get("result", {}).get("image", "")
                    if b64_image:
                        raw_bytes = base64.b64decode(b64_image)

                # Fit to requested target width and height with high-quality Lanczos resampling
                pil_img = Image.open(io.BytesIO(raw_bytes))
                if pil_img.size != (width, height):
                    fitted_img = self._fit_to_aspect(pil_img, width, height)
                    out_buf = io.BytesIO()
                    fitted_img.save(out_buf, format="PNG")
                    return out_buf.getvalue()

                return raw_bytes
        except Exception as exc:
            err_msg = exc.response.text if hasattr(exc, "response") and exc.response is not None else str(exc)
            logger.warning("Cloudflare FLUX image generation initial attempt failed (%s): %s. Attempting distilled retry.", exc, err_msg)
            
            # Direct retry with distilled core prompt
            try:
                distilled = image_prompt[:1400].strip()
                retry_payload = {"prompt": distilled, "steps": 6}
                async with httpx.AsyncClient(timeout=40.0) as client:
                    retry_res = await client.post(self.endpoint, headers=headers, json=retry_payload)
                    retry_res.raise_for_status()
                    retry_bytes = retry_res.content
                    if "application/json" in retry_res.headers.get("content-type", "") or retry_res.content.startswith(b"{"):
                        data = retry_res.json()
                        b64_image = data.get("result", {}).get("image", "")
                        if b64_image:
                            retry_bytes = base64.b64decode(b64_image)

                    pil_img = Image.open(io.BytesIO(retry_bytes))
                    fitted_img = self._fit_to_aspect(pil_img, width, height)
                    out_buf = io.BytesIO()
                    fitted_img.save(out_buf, format="PNG")
                    logger.info("Successfully recovered background via distilled Cloudflare FLUX retry.")
                    return out_buf.getvalue()
            except Exception as retry_exc:
                logger.error("Distilled retry also failed: %s. Using high-aesthetic geometric gradient canvas as final safety net.", retry_exc)

            logger.info("Using high-aesthetic geometric gradient canvas as final safety net.")
            return self._generate_fallback_canvas(width, height)

    async def edit_image(
        self,
        image_bytes: bytes,
        edit_prompt: str,
        width: int = 1024,
        height: int = 1024,
        strength: float = 0.60,
    ) -> bytes:
        """Invoke Cloudflare Image-to-Image diffusion model to perform edits on an existing image dynamically."""
        if not self.api_token or not self.account_id:
            logger.info("Cloudflare credentials not provided. Returning original image.")
            return image_bytes

        img2img_endpoint = (
            f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/@cf/lykon/dreamshaper-8-lcm"
        )
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        # Resize input image cleanly to 512x512 for optimal diffusion input
        pil_in = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        resized_in = self._fit_to_aspect(pil_in, 512, 512)
        buf_in = io.BytesIO()
        resized_in.save(buf_in, format="PNG")

        payload = {
            "prompt": edit_prompt,
            "image": list(buf_in.getvalue()),
            "strength": strength,
            "steps": 8,
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(img2img_endpoint, headers=headers, json=payload)
            response.raise_for_status()

            raw_bytes = response.content
            if "application/json" in response.headers.get("content-type", "") or response.content.startswith(b"{"):
                data = response.json()
                b64_image = data.get("result", {}).get("image", "")
                if b64_image:
                    raw_bytes = base64.b64decode(b64_image)

            pil_out = Image.open(io.BytesIO(raw_bytes))
            fitted_out = self._fit_to_aspect(pil_out, width, height)
            out_buf = io.BytesIO()
            fitted_out.save(out_buf, format="PNG")
            return out_buf.getvalue()

    @staticmethod
    def _fit_to_aspect(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
        """Center crop and resize image to target aspect ratio without distortion."""
        orig_w, orig_h = img.size
        target_ratio = target_w / target_h
        orig_ratio = orig_w / orig_h

        if orig_ratio > target_ratio:
            # Original is wider than target: crop width
            new_w = int(orig_h * target_ratio)
            left = (orig_w - new_w) // 2
            img = img.crop((left, 0, left + new_w, orig_h))
        else:
            # Original is taller than target: crop height
            new_h = int(orig_w / target_ratio)
            top = (orig_h - new_h) // 2
            img = img.crop((0, top, orig_w, top + new_h))

        return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
