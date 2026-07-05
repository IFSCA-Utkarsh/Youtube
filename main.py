"""
==============================================================================
 YOUTUBE STUDIO — DOWNLOAD & PLAY EDITION (v2)
==============================================================================
Entry point for Google Colab / Jupyter.

WHAT THIS IS
    A key-free, API-free YouTube search / channel-browser / downloader /
    player. Search videos, browse a channel's Videos / Playlists / Shorts /
    Live tabs, pick a quality, download the file, and play it back with a
    fast modern Plyr player streamed from a local HTTP server — no YouTube
    iframe embedding is ever used, so "Error 153" cannot occur.

HOW TO RUN
    Option A — Google Colab (recommended):
        1. Upload the whole `youtube_studio_project/` folder (this file +
           the `youtube_studio/` package directory next to it), OR unzip
           `youtube_studio_project.zip` into your Colab session.
        2. Run in a cell:
               %run main.py

    Option B — Import as a module (folder already on disk / sys.path):
        import main  # runs the launch guard automatically
        # or, without auto-launch:
        from youtube_studio import YouTubeStudioApp
        app = YouTubeStudioApp()
        app.display()

PROJECT LAYOUT
    main.py                          <- this file (install + launch)
    youtube_studio/
        __init__.py                  <- package entry point
        config.py                    <- all constants (paths, ports, theme)
        utils.py                     <- formatting / image / filename helpers
        search_engine.py             <- keyword video search
        channel_engine.py            <- channel search + Videos/Playlists/Shorts/Live
        download_engine.py           <- quality discovery + download
        media_server.py              <- local Range-supporting HTTP server
        player.py                    <- fast Plyr-based HTML5 player
        ui_components.py             <- ipywidgets card builders
        app.py                       <- YouTubeStudioApp (3-tab UI)
        local_player_app.py          <- standalone local-file player (bonus)
==============================================================================
"""

import subprocess
import sys


def _install_dependencies():
    """Install/upgrade all required Python packages, then ensure ffmpeg exists."""
    packages = ["yt-dlp", "ipywidgets", "requests"]
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--upgrade", *packages])
        print("✅ Python packages installed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"⚠️ Package installation failed: {exc}")

    import shutil
    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found — installing (required to merge HD video + audio)…")
        try:
            subprocess.run(["apt-get", "-qq", "update"], check=False)
            subprocess.run(["apt-get", "-qq", "install", "-y", "ffmpeg"], check=False)
            if shutil.which("ffmpeg"):
                print("✅ ffmpeg installed successfully.")
            else:
                print("⚠️ ffmpeg installation could not be verified. Downloads above ~360p may fail.")
        except Exception as exc:
            print(f"⚠️ Could not install ffmpeg automatically: {exc}")
    else:
        print("✅ ffmpeg already available.")


def launch():
    """Install dependencies, then build and display the app."""
    _install_dependencies()

    import warnings
    warnings.filterwarnings("ignore")

    # Make sure the sibling `youtube_studio/` package is importable regardless
    # of the current working directory (e.g. when run via %run in Colab).
    import os
    project_dir = os.path.dirname(os.path.abspath(__file__))
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

    from youtube_studio import YouTubeStudioApp

    app = YouTubeStudioApp()
    app.display()
    return app


if __name__ == "__main__":
    launch()
