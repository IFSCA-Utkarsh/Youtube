"""
YouTube Studio — Download & Play Edition
=========================================
A key-free, API-free YouTube search / channel-browser / downloader / player
built for Google Colab (also works in plain Jupyter).

Public entry point:

    from youtube_studio import YouTubeStudioApp
    app = YouTubeStudioApp()
    app.display()
"""

from .app import YouTubeStudioApp

__all__ = ["YouTubeStudioApp"]
__version__ = "2.0.0"
