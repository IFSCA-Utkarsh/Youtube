# YouTube Studio — Download & Play Edition (v2)

A key-free, API-free YouTube search / channel-browser / downloader / player
for Google Colab (also works in plain Jupyter). No YouTube Data API key,
no OAuth — everything is powered by `yt-dlp`.

## What's new in this rewrite

1. **Channel browsing is fixed.** Videos / Playlists / Shorts now reliably
   load, and a new **Live** tab (YouTube's "/streams" tab) has been added.
   The bug was a fragile URL string built from whatever raw link a search
   result returned; the channel engine now always resolves a channel to
   its canonical `https://www.youtube.com/channel/UC.../` URL first, then
   cleanly appends the requested tab. Tabs a channel doesn't have (e.g. no
   Shorts) now return an empty list instead of breaking the UI.
2. **Much faster player.** Downloaded videos now stream from a small local
   HTTP server (with proper `Range` support, so seeking works) into a
   modern [Plyr](https://plyr.io) player, instead of being base64-encoded
   into the notebook output. Playback starts almost instantly regardless
   of file size, and you get a polished UI with speed control, volume,
   and fullscreen.
3. **Clean modular architecture** — one responsibility per file:

```
main.py                       # install deps + launch guard (run this)
youtube_studio/
    __init__.py                # package entry point
    config.py                  # all constants: paths, ports, theme, tab map
    utils.py                   # formatting / image / filename helpers
    search_engine.py            # keyword video search
    channel_engine.py           # channel search + Videos/Playlists/Shorts/Live
    download_engine.py          # quality discovery + download
    media_server.py             # local Range-supporting HTTP server
    player.py                   # fast Plyr-based HTML5 player
    ui_components.py            # ipywidgets card builders
    app.py                      # YouTubeStudioApp (3-tab UI)
    local_player_app.py         # bonus: standalone local-file player
```

## How to run in Google Colab

1. Upload the **whole folder** (`main.py` and the `youtube_studio/`
   directory next to it) — easiest way is to upload the provided
   `youtube_studio_project.zip` and unzip it in a cell:

   ```python
   from google.colab import files
   files.upload()          # choose youtube_studio_project.zip
   !unzip -o youtube_studio_project.zip
   ```

2. Run it:

   ```python
   %run main.py
   ```

That's it — no API key, no config file. The app installs `yt-dlp`,
`ipywidgets`, `requests`, and `ffmpeg` automatically on first run.

## Using it as a plain module (no auto-launch)

```python
import sys
sys.path.insert(0, "/content/youtube_studio_project")  # wherever you unzipped it
from youtube_studio import YouTubeStudioApp

app = YouTubeStudioApp()
app.display()
```

## Standalone local player

If you just want to browse and replay files already sitting in
`youtube_studio_downloads/` (without touching YouTube at all):

```python
from youtube_studio.local_player_app import LocalPlayerApp
LocalPlayerApp().display()
```

## Notes

- **Colab networking**: the local media server binds to `127.0.0.1` and is
  exposed to the notebook's browser tab through Colab's own port-proxy
  (`google.colab.kernel.proxyPort`), which is detected automatically. In
  plain Jupyter it just uses `http://127.0.0.1:<port>/...` directly.
- **ffmpeg** is required to merge separate video+audio streams for
  qualities above ~360p; `main.py` installs it via `apt-get` if missing
  (works out of the box on Colab, which runs as root).
- Every engine call is wrapped in exception handling so a network hiccup
  or a page-structure change on YouTube's side surfaces as a friendly
  status message instead of crashing the notebook.
