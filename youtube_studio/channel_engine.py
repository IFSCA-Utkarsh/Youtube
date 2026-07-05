"""
channel_engine.py
==================
Channel search + channel-tab browsing (Videos / Playlists / Shorts / Live).

What was broken before
-----------------------
The previous implementation built section URLs with
`channel_link.rstrip("/") + f"/{section}"`. That breaks whenever
`channel_link` is not already a clean canonical channel URL — e.g. it still
has a query string attached, already points at a specific tab, or is a
search-result URL that isn't a real channel homepage at all. Any of those
produced a malformed URL, which yt-dlp then failed to extract, so every
"Browse Channel" click silently returned nothing.

The fix
-------
1. Always resolve a channel to its **canonical** `/channel/UC.../` URL
   using the stable `channel_id`, not whatever raw URL search happened to
   return.
2. Before appending a tab, strip query strings, trailing slashes, and any
   tab suffix that might already be present, so we always start from a
   clean base URL.
3. Add a "live" section, which maps to YouTube's own "/streams" tab.
4. If a channel simply doesn't have a given tab (e.g. no Shorts, no Live
   tab), yt-dlp raises a DownloadError — treat that as "0 items" instead of
   propagating an error that breaks the UI.
"""

from __future__ import annotations

import yt_dlp

from .config import SECTION_URL_PATHS, flat_ydl_opts
from .search_engine import parse_video_entries
from .utils import format_views


class ChannelEngine:
    """Searches for channels and browses their Videos/Playlists/Shorts/Live tabs."""

    # ---------------------------------------------------------------- search
    def search_channels(self, query: str, limit: int = 6) -> list[dict]:
        """
        Search YouTube channels by name.

        Implemented against YouTube's own search-results URL with the
        "Type: Channel" filter chip applied (`sp=EgIQAg%3D%3D` is YouTube's
        own base64-encoded filter parameter for that chip) — the same
        yt-dlp mechanism used everywhere else in this project, so no extra
        third-party search library is required.
        """
        if not query or not query.strip():
            raise ValueError("Please enter a channel name to search.")

        from urllib.parse import quote
        search_url = f"https://www.youtube.com/results?search_query={quote(query)}&sp=EgIQAg%3D%3D"

        try:
            with yt_dlp.YoutubeDL(flat_ydl_opts()) as ydl:
                info = ydl.extract_info(search_url, download=False)
        except Exception as exc:
            raise RuntimeError(f"Channel search failed: {exc}") from exc

        entries = (info.get("entries") or [])[:limit] if info else []
        results = []
        for entry in entries:
            if not entry:
                continue
            channel_id = entry.get("channel_id") or entry.get("id")
            if not channel_id:
                continue
            thumbs = entry.get("thumbnails") or []
            thumbnail = thumbs[-1]["url"] if thumbs else ""
            followers = entry.get("channel_follower_count")
            results.append({
                "id": channel_id,
                "title": entry.get("title") or entry.get("channel") or "Unknown Channel",
                "subscribers": format_views(followers) + (" subscribers" if followers else ""),
                "description": entry.get("description") or "",
                "thumbnail": thumbnail,
                # Canonical base URL — always resolvable, always clean.
                "url": f"https://www.youtube.com/channel/{channel_id}",
            })
        return results

    # ------------------------------------------------------------- browsing
    def get_section(self, channel_url: str, section: str, limit: int = 12) -> list[dict]:
        """
        Fetch one tab of a channel: 'videos', 'playlists', 'shorts', or 'live'.
        Returns [] (never raises) if the channel has no such tab.
        """
        if section not in SECTION_URL_PATHS:
            raise ValueError(f"Unknown channel section '{section}'.")

        url = f"{_clean_channel_base(channel_url)}/{SECTION_URL_PATHS[section]}"

        try:
            with yt_dlp.YoutubeDL(flat_ydl_opts()) as ydl:
                info = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError:
            # Tab doesn't exist for this channel (e.g. no Shorts / no Live).
            return []
        except Exception as exc:
            raise RuntimeError(f"Could not load channel {section}: {exc}") from exc

        entries = (info.get("entries") or [])[:limit] if info else []

        if section == "playlists":
            return [_parse_playlist_entry(e) for e in entries if e]
        return parse_video_entries(entries)

    def get_playlist_videos(self, playlist_url: str, limit: int = 12) -> list[dict]:
        """Fetch the videos contained in a playlist."""
        try:
            with yt_dlp.YoutubeDL(flat_ydl_opts()) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
            entries = (info.get("entries") or [])[:limit] if info else []
            return parse_video_entries(entries)
        except Exception as exc:
            raise RuntimeError(f"Could not load playlist videos: {exc}") from exc


def _clean_channel_base(channel_url: str) -> str:
    """Strip query strings, trailing slashes, and any existing tab suffix."""
    base = channel_url.split("?")[0].rstrip("/")
    for path in SECTION_URL_PATHS.values():
        suffix = f"/{path}"
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    return base


def _parse_playlist_entry(entry: dict) -> dict:
    playlist_id = entry.get("id")
    return {
        "id": playlist_id,
        "title": entry.get("title") or "Untitled Playlist",
        "url": entry.get("url") or f"https://www.youtube.com/playlist?list={playlist_id}",
        "video_count": entry.get("playlist_count") or entry.get("entry_count"),
    }
