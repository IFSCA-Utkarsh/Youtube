"""
player.py
=========
Renders a fast, modern video player using Plyr (https://plyr.io) on top of
a plain HTML5 <video> element pointed at the local media server (see
media_server.py). This replaces the old `IPython.display.Video(embed=True)`
approach, which base64-encodes the whole file into notebook output and is
slow for anything but very short clips.

Plyr gives us, for free: a polished modern skin, playback-speed control,
volume/fullscreen, keyboard shortcuts, and (crucially) instant start +
seeking anywhere in the file thanks to the server's HTTP Range support.
"""

from __future__ import annotations

import uuid

from IPython.display import HTML, display

from .config import PLYR_CSS_URL, PLYR_JS_URL


def render_plyr_player(video_url: str, title: str = "", width: int = 720) -> None:
    """Display a Plyr-powered <video> player for `video_url` inline in the notebook."""
    element_id = f"plyr-{uuid.uuid4().hex[:8]}"
    safe_title = (title or "").replace("<", "&lt;").replace(">", "&gt;")

    html = f"""
    <link rel="stylesheet" href="{PLYR_CSS_URL}" />
    <div style="max-width:{width}px;font-family:inherit;">
      {f"<div style='color:#f5f5f7;font-weight:600;font-size:15px;margin:6px 0;'>{safe_title}</div>" if safe_title else ""}
      <video id="{element_id}" playsinline controls style="width:100%;border-radius:10px;overflow:hidden;">
        <source src="{video_url}" type="video/mp4" />
        Your browser does not support HTML5 video.
      </video>
    </div>
    <script src="{PLYR_JS_URL}"></script>
    <script>
      (function() {{
        function init() {{
          const el = document.getElementById("{element_id}");
          if (el && window.Plyr) {{
            new Plyr(el, {{
              settings: ["quality", "speed", "loop"],
              speed: {{ selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] }},
            }});
          }} else {{
            setTimeout(init, 150);
          }}
        }}
        init();
      }})();
    </script>
    """
    display(HTML(html))


def render_playback_error(message: str, file_path: str = "") -> None:
    """Fallback message shown when the player itself cannot be rendered."""
    extra = f"<br>The file is still saved at: <code>{file_path}</code>" if file_path else ""
    display(HTML(f"<p style='color:#e57373;'>⚠️ {message}{extra}</p>"))
