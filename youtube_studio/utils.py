"""
utils.py
========
Small, dependency-light helper functions shared across the project:
number/time formatting, thumbnail URL construction, image fetching, and
environment detection. Nothing in this module talks to yt-dlp.
"""

from __future__ import annotations

import re
import unicodedata

import requests


def in_colab() -> bool:
    """Return True when running inside a Google Colab kernel."""
    try:
        import google.colab  # noqa: F401
        return True
    except ImportError:
        return False


def format_duration(seconds) -> str:
    """Convert raw seconds into a clean H:MM:SS / M:SS string."""
    if seconds is None:
        return "N/A"
    try:
        seconds = int(seconds)
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
    except (ValueError, TypeError):
        return "N/A"


def format_views(count) -> str:
    """Convert a raw count (views, subscribers, etc.) into a compact string."""
    if not count:
        return "N/A"
    try:
        count = int(count)
        for unit, threshold in (("B", 1_000_000_000), ("M", 1_000_000), ("K", 1_000)):
            if count >= threshold:
                return f"{count / threshold:.1f}{unit}"
        return str(count)
    except (ValueError, TypeError):
        return "N/A"


def thumbnail_url(video_id: str, quality: str = "hqdefault") -> str:
    """Public, key-free thumbnail CDN URL used by every YouTube page."""
    return f"https://i.ytimg.com/vi/{video_id}/{quality}.jpg"


def fetch_image_bytes(url: str, timeout: int = 6):
    """Download an image and return raw bytes, or None on any failure."""
    if not url:
        return None
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content
    except Exception:
        return None


def safe_filename(name: str, max_length: int = 120) -> str:
    """Sanitize an arbitrary title into a filesystem-safe filename fragment."""
    if not name:
        return "video"
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    cleaned = re.sub(r"[^A-Za-z0-9 ._-]+", "", normalized).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:max_length] or "video"
