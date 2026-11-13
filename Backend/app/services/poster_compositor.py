"""Poster compositor engine for layout and typography layering."""

import io
import re
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont


class PosterCompositor:
    """Composites visual posters with typography and brand marks."""

    @staticmethod
    def _clean_text(text: str) -> str:
        """Strips unsupported glyphs and emojis."""
        if not text:
            return ""
        cjk_pattern = r"[\u4e00-\u9fff\u3040-\u30ff\u3400-\u4dbf\uac00-\ud7af\uff00-\uffef]+"
        cleaned = re.sub(cjk_pattern, "", str(text))
        cleaned = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\ufe0f]", "", cleaned)
        return re.sub(r" +", " ", cleaned).strip()

    @staticmethod
    def _wrap_text(text: str, max_chars_per_line: int = 28) -> str:
        """Wraps text into centered lines."""
        sanitized = PosterCompositor._clean_text(text)
        words = sanitized.split()
        lines = []
        current_line = []
        current_len = 0

        for word in words:
            if current_len + len(word) + 1 <= max_chars_per_line:
                current_line.append(word)
                current_len += len(word) + 1
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_len = len(word)
        if current_line:
            lines.append(" ".join(current_line))
        return "\n".join(lines)

    @staticmethod
    def _get_font(style: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Loads system TrueType font or fallback."""
        candidates = {
            "serif_bold": ["georgiab.ttf", "timesbd.ttf", "arialbd.ttf"],
            "serif_italic": ["georgiai.ttf", "georgia.ttf", "times.ttf"],
            "sans_bold": ["segoeuib.ttf", "arialbd.ttf"],
            "sans_regular": ["segoeui.ttf", "arial.ttf"],
        }
        search_list = candidates.get(style, ["georgiab.ttf", "arialbd.ttf", "arial.ttf"])
        windows_fonts = Path("C:/Windows/Fonts")
        for font_file in search_list:
            font_path = windows_fonts / font_file
            if font_path.exists():
                try:
                    return ImageFont.truetype(str(font_path), size=size)
                except Exception:
                    continue
        return ImageFont.load_default()

    @staticmethod
    def _parse_color(hex_str: Optional[str], default_rgba: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        """Converts hex color string to RGBA tuple."""
        if not hex_str:
            return default_rgba
        try:
            h = str(hex_str).strip().lstrip("#")
            if len(h) == 3:
                h = "".join([c * 2 for c in h])
            if len(h) == 6:
                r = int(h[0:2], 16)
                g = int(h[2:4], 16)
                b = int(h[4:6], 16)
                return (r, g, b, 255)
        except Exception:
            pass
        return default_rgba

    def composite_poster(
        self,
        background_bytes: bytes,
        plan: any,
        primary_color: str = "#F59E0B",
        secondary_color: str = "#FFFFFF",
        quote_color: Optional[str] = None,
        logo_bytes: Optional[bytes] = None,
        quote_y_ratio: Optional[float] = None,
        quote_scale: Optional[float] = None,
        headline_y_ratio: Optional[float] = None,
        headline_scale: Optional[float] = None,
    ) -> bytes:
        """Composites typography, brand logos, and contrast shading onto background image."""
        base_img = Image.open(io.BytesIO(background_bytes)).convert("RGBA")
        width, height = base_img.size
        center_x = width // 2

        # 1. Determine Layout Placement (Top vs Bottom safe space)
        is_top_placement = (headline_y_ratio is not None and headline_y_ratio < 0.45)
        if is_top_placement:
            y_r = min(0.14, max(0.08, headline_y_ratio if headline_y_ratio is not None else 0.10))
            cursor_y = int(height * y_r)
        else:
            # Bottom safe zone: respect calculated ratio clamped safely to prevent cut-off
            y_r = max(0.45, min(0.82, headline_y_ratio if headline_y_ratio is not None else 0.76))
            cursor_y = int(height * y_r)

        # 2. Ambient Shading Gradient in typography zone (never darkening subject)
        vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        v_draw = ImageDraw.Draw(vignette)
        if is_top_placement:
            v_end = int(height * 0.36)
            for y in range(0, v_end):
                dist = (v_end - y) / float(v_end)
                alpha = int(125 * (dist ** 1.6))
                v_draw.line([(0, y), (width, y)], fill=(8, 12, 22, alpha))
        else:
            v_start = int(height * 0.58)
            for y in range(v_start, height):
                t = (y - v_start) / float(height - v_start)
                alpha = int(135 * (t ** 1.7))
                v_draw.line([(0, y), (width, y)], fill=(8, 12, 22, alpha))

        composed = Image.alpha_composite(base_img, vignette)
        draw = ImageDraw.Draw(composed)

        # 3. Brand Logo Placement (Top-right corner with crisp sizing, matching gold-standard reference poster)
        if logo_bytes:
            try:
                logo_img = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
                lw = 110
                lh = int(logo_img.height * (lw / float(logo_img.width)))
                resized_logo = logo_img.resize((lw, lh), Image.Resampling.LANCZOS)
                logo_x = width - lw - 52
                logo_y = 48
                composed.alpha_composite(resized_logo, (logo_x, logo_y))
            except Exception:
                pass

        # 4. Color Palette & Scaling
        c_accent = self._parse_color(primary_color, (245, 158, 11, 255))
        c_headline = self._parse_color(secondary_color, (255, 255, 255, 255))
        h_scale = headline_scale if headline_scale is not None else 1.0
        q_scale = quote_scale if quote_scale is not None else 1.0

        # 5. Editorial Category / Occasion Tagline (Dynamically directed by LLM plan)
        raw_tag = getattr(plan, "sub_tagline", None) or getattr(plan, "category_tag", None)
        tag_label = self._clean_text(raw_tag) if raw_tag else None

        if tag_label:
            tag_font = self._get_font("sans_bold", max(11, int(14 * h_scale)))
            spaced_tag = f"—   {'  '.join(tag_label.split())}   —"
            draw.text((center_x, cursor_y), spaced_tag, fill=c_accent, font=tag_font, anchor="ma")
            cursor_y += int(30 * h_scale)

        # 6. Hero Headline: Centered, Elegantly Wrapped, Guaranteed Margins (Zero off-screen truncation)
        raw_headline = getattr(plan, "headline", "Elevate Your Vision").strip()
        raw_headline = " ".join(raw_headline.split())

        max_allowed_w = int(width * 0.84)
        base_h_size = max(24, int(42 * h_scale))

        wrapped_headline = self._wrap_text(raw_headline, max_chars_per_line=18)
        headline_font = self._get_font("serif_bold", base_h_size)
        hb = draw.multiline_textbbox((0, 0), wrapped_headline, font=headline_font, align="center", spacing=int(8 * h_scale))
        hw = hb[2] - hb[0]

        while hw > max_allowed_w and base_h_size > 22:
            base_h_size -= 2
            headline_font = self._get_font("serif_bold", base_h_size)
            hb = draw.multiline_textbbox((0, 0), wrapped_headline, font=headline_font, align="center", spacing=int(8 * h_scale))
            hw = hb[2] - hb[0]

        # Chiaroscuro 3D Ambient Drop Shadow
        for dx, dy in [(-2, -1), (2, -1), (-2, 2), (2, 2), (0, 3), (0, 4)]:
            draw.multiline_text(
                (center_x + dx, cursor_y + dy),
                wrapped_headline,
                font=headline_font,
                fill=(0, 0, 0, 230),
                align="center",
                anchor="ma",
                spacing=int(8 * h_scale),
            )

        # Draw main headline in radiant luxury gold or scanned headline color
        draw.multiline_text(
            (center_x, cursor_y),
            wrapped_headline,
            font=headline_font,
            fill=c_headline,
            align="center",
            anchor="ma",
            spacing=int(8 * h_scale),
        )

        headline_h = hb[3] - hb[1]
        cursor_y += headline_h + int(20 * h_scale)

        # 7. Editorial Luxury Quote (Zero Pill Box Clutter)
        quote_font = self._get_font("serif_italic", max(18, int(24 * q_scale)))
        raw_quote = getattr(plan, "story_quote", None) or getattr(plan, "quote", "In quiet stillness, wisdom illuminates the path ahead.")
        clean_q = str(raw_quote).strip().strip('"\'“”').strip()
        wrapped_quote = self._wrap_text(clean_q, max_chars_per_line=int(32 / q_scale) if q_scale > 1.0 else 32)

        # Subtle decorative divider line
        div_y = cursor_y + 8
        draw.line([(center_x - 50, div_y), (center_x + 50, div_y)], fill=c_accent, width=1)
        draw.ellipse([center_x - 4, div_y - 3, center_x + 4, div_y + 4], fill=c_accent)
        cursor_y = div_y + 20

        # Chiaroscuro 3D Ambient Drop Shadow for 100% legibility
        c_quote = self._parse_color(quote_color, (255, 246, 224, 255))
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, 2), (0, 3)]:
            draw.multiline_text(
                (center_x + dx, cursor_y + dy),
                wrapped_quote,
                font=quote_font,
                fill=(0, 0, 0, 230),
                align="center",
                anchor="ma",
                spacing=8,
            )

        draw.multiline_text(
            (center_x, cursor_y),
            wrapped_quote,
            font=quote_font,
            fill=c_quote,
            align="center",
            anchor="ma",
            spacing=8,
        )

        # Export high-res PNG
        output_buffer = io.BytesIO()
        composed.convert("RGB").save(output_buffer, format="PNG", quality=95)
        return output_buffer.getvalue()
