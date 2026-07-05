"""
download_engine.py
===================
Discovers available video qualities and performs the actual download +
audio/video merge (via ffmpeg, invoked automatically by yt-dlp).

Bot-detection handling
-----------------------
Cloud IPs (Colab, AWS, GCP, etc.) are frequently hit with YouTube's
"Sign in to confirm you're not a bot" error, independent of which video is
requested. Every yt-dlp call in this module goes through
`config.probe_ydl_opts()` / a locally-built opts dict that both include:

  1. `player_client: ["android", "web"]` — fixes most cases with zero setup.
  2. A `cookiefile` pointing at `cookies.txt`, automatically picked up if
     that file exists (see config.py for how to create one).

If a request still fails with that specific error, `_friendly_error()`
rewrites yt-dlp's raw message into short, actionable guidance instead of
the full technical dump.
"""

from __future__ import annotations

import os

import yt_dlp

from .config import DOWNLOAD_DIR, COOKIES_FILE, base_extractor_args, cookie_opts, probe_ydl_opts

_BOT_CHECK_MARKER = "Sign in to confirm"


class DownloadEngine:
    """Handles quality discovery and downloading of a single video."""

    def get_available_qualities(self, video_id: str) -> list[int]:
        """Return the list of available video heights (resolutions), high to low."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            with yt_dlp.YoutubeDL(probe_ydl_opts()) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as exc:
            raise RuntimeError(_friendly_error(exc)) from exc

        heights = set()
        for fmt in info.get("formats", []) or []:
            height = fmt.get("height")
            vcodec = fmt.get("vcodec")
            if height and vcodec and vcodec != "none":
                heights.add(int(height))

        if not heights:
            raise RuntimeError("No downloadable video qualities were found for this video.")
        return sorted(heights, reverse=True)

    def download_video(self, video_id: str, height: int, progress_hook=None) -> dict:
        """
        Download the given video at (up to) the requested height, merging
        video + audio into a single .mp4 via ffmpeg.

        Returns: {"path": str, "size_mb": float}
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        out_template = os.path.join(DOWNLOAD_DIR, f"{video_id}_{height}p.%(ext)s")

        ydl_opts = {
            "format": f"bestvideo[height<={height}]+bestaudio/best[height<={height}]",
            "outtmpl": out_template,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }
        ydl_opts.update(base_extractor_args())
        ydl_opts.update(cookie_opts())
        if progress_hook:
            ydl_opts["progress_hooks"] = [progress_hook]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
        except Exception as exc:
            raise RuntimeError(_friendly_error(exc)) from exc

        base, _ext = os.path.splitext(filename)
        final_path = base + ".mp4"
        if not os.path.exists(final_path):
            final_path = filename  # no merge occurred; use the original extension

        size_mb = round(os.path.getsize(final_path) / (1024 * 1024), 1)
        return {"path": final_path, "size_mb": size_mb}


def _friendly_error(exc: Exception) -> str:
    """Rewrite YouTube's bot-check error into short, actionable guidance."""
    text = str(exc)
    if _BOT_CHECK_MARKER in text:
        cookie_hint = (
            f"'{COOKIES_FILE}' was not found next to your notebook."
            if not os.path.isfile(COOKIES_FILE)
            else f"'{COOKIES_FILE}' was found but YouTube still rejected the request — it may be expired; export a fresh one."
        )
        return (
            "YouTube is blocking this request as a suspected bot (common on Colab's "
            f"cloud IPs, unrelated to the video itself). {cookie_hint} "
            f"Export cookies.txt from a logged-in browser (e.g. the 'Get cookies.txt LOCALLY' "
            f"extension) and upload it into this session's working directory as '{COOKIES_FILE}', "
            "then try again."
        )
    return f"Download failed: {text}"
