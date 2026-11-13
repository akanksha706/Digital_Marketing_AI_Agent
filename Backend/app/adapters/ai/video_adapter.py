"""AI video generator adapter powered by Wan 2.2 and Wan 2.1 Fast Diffusion."""

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import Optional
from gradio_client import Client, handle_file

from app.core.config import settings
from app.interfaces.video_generator import AbstractVideoGenerator

logger = logging.getLogger(__name__)


class VideoGeneratorAdapter(AbstractVideoGenerator):
    """Generates authentic AI-diffused full-motion video using Wan 2.2 / Wan 2.1."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_token: Optional[str] = None,
    ):
        self.model_name = model_name or settings.VIDEO_MODEL or "Wan-AI/Wan2.2-TI2V-5B"
        self.api_token = (
            api_token
            or settings.HUGGINGFACE_API_KEY
            or getattr(settings, "HUGGING_FACE_TOKEN", "")
            or os.environ.get("HUGGINGFACE_API_KEY")
            or os.environ.get("HUGGING_FACE_TOKEN")
            or os.environ.get("HF_TOKEN")
            or ""
        )

    def _generate_via_wan_space(
        self,
        source_image_path: Path,
        prompt: str,
        output_path: Path,
        duration_seconds: int = 4,
    ) -> bool:
        """Invokes Wan 2.2 / Wan 2.1 Fast diffusion to produce authentic full-motion video."""
        space_endpoints = [
            "zerogpu-aoti/wan2-2-fp8da-aoti-faster",
            "r3gm/wan2-2-fp8da-aoti-preview",
            "r3gm/wan2-2-fp8da-aoti-preview2",
            "Lightricks/ltx-video-distilled",
        ]

        # Clean prefix artifacts from LLMs (e.g. 'Actionable video motion prompt:')
        import re
        raw_clean = re.sub(r"^(Actionable video motion prompt|Video motion prompt|Motion prompt)\s*:?\s*", "", prompt.strip(), flags=re.I)
        raw_clean = re.sub(r"^[\"'\`]+|[\"'\`]+$", "", raw_clean).strip()

        clean_motion_prompt = (
            f"{raw_clean}. High motion dynamics, authentic physical character movement, expressive human eyes, gentle breathing, "
            f"natural gestures, rippling fluid motion, alive environment, ultra-crisp focus, photorealistic masterpiece"
        )

        neg_prompt = (
            "blurry, smudged faces, distorted eyes, bad anatomy, deformed hands, hallucinated limbs, "
            "low quality, noisy, jitter, floating objects, cropped head, weird grinning, motionless statue, static still picture, "
            "Chinese text, Japanese characters, Asian symbols, Kanji, Hanzi, Asian calligraphy, foreign subtitles, oriental letters"
        )

        # Prioritize authenticated account token (uses fresh account / PRO quota first), then anonymous fallback
        token_candidates = []
        if self.api_token:
            token_candidates.append(self.api_token)
        token_candidates.append(None)

        for space_id in space_endpoints:
            for tok in token_candidates:
                try:
                    logger.info("Attempting authentic neural motion video synthesis via space: %s (token=%s)", space_id, bool(tok))
                    client = Client(
                        space_id,
                        token=tok,
                        httpx_kwargs={"timeout": 180.0},
                    )

                    img_file = handle_file(str(source_image_path))

                    if "ltx-video" in space_id.lower():
                        submit_kwargs = {
                            "prompt": clean_motion_prompt,
                            "negative_prompt": neg_prompt,
                            "input_image_filepath": img_file,
                            "input_video_filepath": None,
                            "height_ui": 704,
                            "width_ui": 512,
                            "mode": "image-to-video",
                            "duration_ui": float(min(duration_seconds, 3.5)),
                            "ui_frames_to_use": 9,
                            "seed_ui": 42,
                            "randomize_seed": True,
                            "ui_guidance_scale": 1.2,
                            "improve_texture_flag": True,
                            "api_name": "/image_to_video",
                        }
                    else:
                        submit_kwargs = {
                            "input_image": img_file,
                            "prompt": clean_motion_prompt,
                            "steps": 6,
                            "negative_prompt": neg_prompt,
                            "duration_seconds": float(min(duration_seconds, 3.5)),
                            "guidance_scale": 1.5,
                            "guidance_scale_2": 1.5,
                            "seed": 42,
                            "randomize_seed": True,
                            "api_name": "/generate_video",
                        }

                        if "r3gm" in space_id:
                            submit_kwargs["last_image"] = img_file
                            submit_kwargs["quality"] = 6
                            submit_kwargs["scheduler"] = "UniPCMultistep"
                            submit_kwargs["flow_shift"] = 3.0
                            submit_kwargs["frame_multiplier"] = "16"
                            submit_kwargs["video_component"] = True
                            submit_kwargs["safe_mode"] = True
                            submit_kwargs["enable_safety_checker"] = True

                    job = client.submit(**submit_kwargs)
                    res = job.result(timeout=180.0)

                    # Robustly unwrap video path from gradio result (handles nested dicts/tuples/lists)
                    temp_video_path = res
                    while isinstance(temp_video_path, (dict, list, tuple)):
                        if isinstance(temp_video_path, dict):
                            temp_video_path = (
                                temp_video_path.get("video")
                                or temp_video_path.get("path")
                                or (next(iter(temp_video_path.values())) if temp_video_path else None)
                            )
                        elif isinstance(temp_video_path, (list, tuple)):
                            temp_video_path = temp_video_path[0] if temp_video_path else None

                    if temp_video_path and os.path.exists(str(temp_video_path)):
                        shutil.copyfile(str(temp_video_path), output_path)
                        logger.info("Successfully produced neural full-motion video (%s bytes): %s", output_path.stat().st_size, output_path)
                        self.model_name = "LTX-Video Distilled (Fast Character Motion)" if "ltx" in space_id.lower() else "Wan 2.2 Neural Diffusion"
                        return True
                except Exception as space_err:
                    logger.warning("Space '%s' (token=%s) attempt failed: %s. Trying next...", space_id, bool(tok), space_err)

        return False

    async def generate_video(
        self,
        prompt: str,
        output_path: Path,
        duration_seconds: int = 4,
        source_image_path: Optional[Path] = None,
    ) -> bool:
        """Invokes Wan 2.2 / Wan 2.1 Fast ZeroGPU diffusion to produce authentic full-motion video."""
        if not source_image_path or not source_image_path.exists():
            logger.warning("Source image not found for video generation: %s", source_image_path)
            return False

        try:
            success = await asyncio.to_thread(
                self._generate_via_wan_space,
                source_image_path=source_image_path,
                prompt=prompt,
                output_path=output_path,
                duration_seconds=duration_seconds,
            )
            return success
        except Exception as err:
            logger.error("Full-motion Wan video generation thread failed: %s", err, exc_info=True)
            return False
