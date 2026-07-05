"""
download_engine.py
===================
Discovers available video qualities and performs the actual download +
audio/video merge (via ffmpeg, invoked automatically by yt-dlp).
"""

from __future__ import annotations

import os

import yt_dlp

from .config import DOWNLOAD_DIR, YDL_PROBE_OPTS


class DownloadEngine:
    """Handles quality discovery and downloading of a single video."""

    def get_available_qualities(self, video_id: str) -> list[int]:
        """Return the list of available video heights (resolutions), high to low."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            with yt_dlp.YoutubeDL(YDL_PROBE_OPTS) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as exc:
            raise RuntimeError(f"Could not fetch available qualities: {exc}") from exc

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
        if progress_hook:
            ydl_opts["progress_hooks"] = [progress_hook]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
        except Exception as exc:
            raise RuntimeError(f"Download failed: {exc}") from exc

        base, _ext = os.path.splitext(filename)
        final_path = base + ".mp4"
        if not os.path.exists(final_path):
            final_path = filename  # no merge occurred; use the original extension

        size_mb = round(os.path.getsize(final_path) / (1024 * 1024), 1)
        return {"path": final_path, "size_mb": size_mb}
