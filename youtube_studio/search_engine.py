"""
search_engine.py
================
Keyword video search, backed entirely by yt-dlp's `ytsearch` pseudo-extractor.
No YouTube Data API, no API key.
"""

from __future__ import annotations

import yt_dlp

from .config import flat_ydl_opts
from .utils import format_duration, format_views, thumbnail_url


class SearchEngine:
    """Searches YouTube videos by keyword."""

    def search_videos(self, query: str, limit: int = 8) -> list[dict]:
        if not query or not query.strip():
            raise ValueError("Please enter a search keyword.")
        try:
            with yt_dlp.YoutubeDL(flat_ydl_opts()) as ydl:
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            return _parse_video_entries(info.get("entries", []) if info else [])
        except Exception as exc:
            raise RuntimeError(f"Video search failed: {exc}") from exc


def _parse_video_entries(entries) -> list[dict]:
    """Normalize raw yt-dlp entries into a clean, UI-ready video dict list."""
    results = []
    for entry in entries:
        if not entry:
            continue
        video_id = entry.get("id")
        if not video_id:
            continue
        results.append({
            "id": video_id,
            "title": entry.get("title", "Untitled"),
            "channel": entry.get("channel") or entry.get("uploader") or "Unknown",
            "duration": format_duration(entry.get("duration")),
            "views": format_views(entry.get("view_count")) + (
                " views" if entry.get("view_count") else ""
            ),
            "thumbnail": thumbnail_url(video_id),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "is_live": bool(entry.get("is_live") or entry.get("live_status") == "is_live"),
        })
    return results


# Exposed for reuse by channel_engine.py so both modules build identical
# video dicts.
parse_video_entries = _parse_video_entries
