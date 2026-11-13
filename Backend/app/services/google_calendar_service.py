"""Official Google Calendar Service.
Fetches real-time festival and holiday events directly from Google Calendar's live public calendar feeds,
strictly filters and sorts the nearest 5 upcoming festivals, and provides AI-powered design prompts & autocompletions.
Zero hardcoded festival dictionaries.
"""

import logging
import re
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.prompts import build_autocomplete_prompt, build_calendar_festival_prompt

logger = logging.getLogger(__name__)

# Google Calendar official public iCal holiday feeds
GCAL_FEEDS = {
    "indian": "https://calendar.google.com/calendar/ical/en.indian%23holiday%40group.v.calendar.google.com/public/basic.ics",
    "global": "https://calendar.google.com/calendar/ical/en.usa%23holiday%40group.v.calendar.google.com/public/basic.ics",
}

# Administrative / non-festival days to exclude from marketing design celebrations
EXCLUDED_NAMES = {
    "daylight saving time ends",
    "daylight saving time starts",
    "election day",
    "tax day",
    "inauguration day",
    "veterans day",
    "naraka chaturdasi",
    "martin luther king jr. day (substitute)",
    "memorial day (substitute)",
    "independence day (substitute)",
    "labor day (substitute)",
    "veterans day (substitute)",
    "christmas day (substitute)",
    "new year's day (substitute)",
}


class GoogleCalendarService:
    """Official Google Calendar live integration service."""

    _cached_events: List[Dict[str, Any]] = []
    _cache_time: Optional[datetime] = None
    _autocomplete_cache: Dict[str, str] = {}

    @classmethod
    async def fetch_from_google_calendar(cls) -> List[Dict[str, Any]]:
        """Fetch live events directly from Google Calendar official feeds."""
        now = datetime.now()
        # Cache for 6 hours
        if cls._cached_events and cls._cache_time and (now - cls._cache_time) < timedelta(hours=6):
            return cls._cached_events

        today = date.today()
        # Fallback if system date is before 2026
        if today.year < 2026:
            today = date(2026, 10, 27)

        events: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=12.0) as client:
            for category, url in GCAL_FEEDS.items():
                try:
                    res = await client.get(url)
                    if res.status_code != 200:
                        continue
                    text = res.text
                    # Parse iCalendar VEVENT blocks
                    for block in text.split("BEGIN:VEVENT")[1:]:
                        summary_m = re.search(r"SUMMARY:(.+)", block)
                        dtstart_m = re.search(r"DTSTART(?:;VALUE=DATE)?:(\d{8})", block)
                        if summary_m and dtstart_m:
                            summary = summary_m.group(1).strip()
                            clean_name = summary.split("(")[0].strip()
                            # Clean up slashes like "Diwali/Deepavali" -> "Diwali"
                            if "/" in clean_name:
                                clean_name = clean_name.split("/")[0].strip()

                            if clean_name.lower() in EXCLUDED_NAMES:
                                continue

                            dt_str = dtstart_m.group(1).strip()
                            try:
                                ev_date = datetime.strptime(dt_str, "%Y%m%d").date()
                                if ev_date >= today:
                                    delta = (ev_date - today).days
                                    time_tag = "Today" if delta == 0 else f"In {delta} day" if delta == 1 else f"In {delta} days"
                                    events.append({
                                        "id": f"gcal_{re.sub(r'[^a-zA-Z0-9]', '_', clean_name.lower())}_{ev_date.year}",
                                        "name": clean_name,
                                        "date": ev_date.isoformat(),
                                        "days_until": delta,
                                        "category": category,
                                        "badge": "Festival" if category == "indian" else "Celebration",
                                        "prompt": build_calendar_festival_prompt(clean_name, ev_date.year, format_type="poster"),
                                        "poster_prompt": build_calendar_festival_prompt(clean_name, ev_date.year, format_type="poster"),
                                        "video_prompt": build_calendar_festival_prompt(clean_name, ev_date.year, format_type="video"),
                                        "time_tag": time_tag,
                                        "formatted_date": ev_date.strftime("%b %d, %Y"),
                                    })
                            except Exception:
                                pass
                except Exception as e:
                    logger.error(f"Error fetching Google Calendar feed {category}: {e}")

        # Sort strictly by nearest date ascending
        events.sort(key=lambda x: x["days_until"])

        # Deduplicate names keeping the closest occurrence
        seen = set()
        deduped = []
        for ev in events:
            if ev["name"].lower() not in seen:
                seen.add(ev["name"].lower())
                deduped.append(ev)

        if deduped:
            cls._cached_events = deduped
            cls._cache_time = now

        return cls._cached_events

    @classmethod
    async def get_upcoming_occasions(
        cls,
        limit: int = 5,
        category: Optional[str] = None,
        format_type: Optional[str] = "poster",
    ) -> List[Dict[str, Any]]:
        """Return strictly the top 5 nearest festivals from Google Calendar with format-adapted prompts."""
        events = await cls.fetch_from_google_calendar()

        if category and category != "all":
            events = [e for e in events if e.get("category") == category]

        result = []
        is_video = str(format_type).lower() == "video"
        for ev in events[:limit]:
            item = dict(ev)
            if is_video:
                item["prompt"] = item.get("video_prompt") or item.get("prompt")
            else:
                item["prompt"] = item.get("poster_prompt") or item.get("prompt")
            result.append(item)

        return result

    @classmethod
    async def get_smart_autocomplete(cls, text: str) -> Optional[str]:
        """Generate smart ghost-text completion using LLaMA 3.1 Language Model."""
        clean_text = text.strip()
        if not clean_text or len(clean_text) < 2:
            return None

        cache_key = text.lower()
        if cache_key in cls._autocomplete_cache:
            return cls._autocomplete_cache[cache_key]

        prompt = build_autocomplete_prompt(text)
        endpoint = f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/ai/run/{settings.TEXT_MODEL}"
        headers = {
            "Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 25,
            "temperature": 0.2,
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(endpoint, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                raw_completion = data.get("result", {}).get("response", "").strip()
                raw_completion = raw_completion.strip(' "\'“”—-')

                if text.endswith(" "):
                    raw_completion = raw_completion.lstrip()
                else:
                    raw_completion = " " + raw_completion.lstrip()

                cls._autocomplete_cache[cache_key] = raw_completion
                return raw_completion
        except Exception as e:
            logger.warning(f"Autocomplete AI model call failed: {e}")
            return None
