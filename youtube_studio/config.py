"""
config.py
=========
Global configuration constants shared across every module. Keeping these in
one place means folder paths, timeouts, and UI theming can be changed
without touching business logic elsewhere.
"""

import os

# --------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------
# Where downloaded video files live. Relative path -> works unmodified in
# both Google Colab and plain Jupyter.
DOWNLOAD_DIR = os.environ.get("YT_STUDIO_DOWNLOAD_DIR", "youtube_studio_downloads")

# Extensions the local player / folder scanner treats as playable video.
VIDEO_EXTENSIONS = (".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v")

# --------------------------------------------------------------------------
# Local media server (used to stream downloaded files to the Plyr player
# with proper HTTP Range support, instead of slow base64 embedding)
# --------------------------------------------------------------------------
MEDIA_SERVER_HOST = "127.0.0.1"
MEDIA_SERVER_PORT_RANGE = (8600, 8700)  # first free port in this range is used

# --------------------------------------------------------------------------
# Channel browsing
# --------------------------------------------------------------------------
# Display order of the tabs shown for a selected channel. "live" maps to
# YouTube's own "/streams" tab under the hood (see channel_engine.py).
CHANNEL_SECTIONS = ("videos", "playlists", "shorts", "live")

SECTION_URL_PATHS = {
    "videos": "videos",
    "playlists": "playlists",
    "shorts": "shorts",
    "live": "streams",
}

# --------------------------------------------------------------------------
# yt-dlp options
# --------------------------------------------------------------------------
# Fast, "flat" (metadata-only, no per-video network hit) options used for
# every listing call: search results, channel tabs, playlists.
YDL_FLAT_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "extract_flat": "in_playlist",
    "noplaylist": True,
    "ignoreerrors": True,
}

# Options used when we need full per-video metadata (available formats).
YDL_PROBE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "noplaylist": True,
    "ignoreerrors": False,
}

# --------------------------------------------------------------------------
# Player (Plyr — https://github.com/sampotts/plyr)
# --------------------------------------------------------------------------
PLYR_VERSION = "3.7.8"
PLYR_CSS_URL = f"https://cdn.plyr.io/{PLYR_VERSION}/plyr.css"
PLYR_JS_URL = f"https://cdn.plyr.io/{PLYR_VERSION}/plyr.js"

# --------------------------------------------------------------------------
# Theme
# --------------------------------------------------------------------------
THEME_CSS = """
<style>
.ytstudio-card {
    background: #1b1e2b;
    border-radius: 14px;
    padding: 10px;
    margin: 8px 4px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.35);
    transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
    border: 1px solid #2b2f45;
}
.ytstudio-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.5);
}
.ytstudio-title { color: #f5f5f7; font-weight: 600; font-size: 14px; line-height: 1.3em; }
.ytstudio-meta  { color: #9aa0b4; font-size: 12px; margin-top: 4px; }
.ytstudio-badge {
    display: inline-block; background: #2b2f45; color: #9aa0b4;
    border-radius: 6px; padding: 1px 6px; font-size: 11px; margin-right: 4px;
}
.ytstudio-header {
    background: linear-gradient(90deg, #ff512f, #dd2476);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
}
</style>
"""
