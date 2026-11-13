"""Core system configuration, security, errors, and centralized prompt registry."""

from app.core.config import settings
from app.core.errors import to_user_friendly_error
from app.core.prompts import (
    POSTER_DIRECTOR_SYSTEM_PROMPT,
    POSTER_USER_PROMPT_TEMPLATE,
    CALENDAR_FESTIVAL_PROMPT_TEMPLATE,
    AUTOCOMPLETE_PROMPT_TEMPLATE,
    VIDEO_MOTION_SYSTEM_PROMPT,
    build_poster_director_system_prompt,
    build_poster_user_prompt,
    build_calendar_festival_prompt,
    build_autocomplete_prompt,
    enhance_image_prompt,
)

__all__ = [
    "settings",
    "to_user_friendly_error",
    "POSTER_DIRECTOR_SYSTEM_PROMPT",
    "POSTER_USER_PROMPT_TEMPLATE",
    "CALENDAR_FESTIVAL_PROMPT_TEMPLATE",
    "AUTOCOMPLETE_PROMPT_TEMPLATE",
    "VIDEO_MOTION_SYSTEM_PROMPT",
    "build_poster_director_system_prompt",
    "build_poster_user_prompt",
    "build_calendar_festival_prompt",
    "build_autocomplete_prompt",
    "enhance_image_prompt",
]
