"""
local_player_app.py
====================
Standalone utility: scans DOWNLOAD_DIR for previously downloaded video
files and plays any selected one with the same fast Plyr-based player used
by the main app (see player.py / media_server.py). No YouTube access at
all — purely local files.
"""

from __future__ import annotations

import os

import ipywidgets as widgets
from IPython.display import HTML, clear_output, display

from .config import DOWNLOAD_DIR, THEME_CSS, VIDEO_EXTENSIONS
from .media_server import MediaServer
from .player import render_playback_error, render_plyr_player


def list_downloaded_videos(folder: str = DOWNLOAD_DIR) -> list[dict]:
    """Scan `folder` for video files. Returns [] (never raises) if missing."""
    if not os.path.isdir(folder):
        return []
    videos = []
    for filename in sorted(os.listdir(folder)):
        if not filename.lower().endswith(VIDEO_EXTENSIONS):
            continue
        full_path = os.path.join(folder, filename)
        if not os.path.isfile(full_path):
            continue
        try:
            size_mb = round(os.path.getsize(full_path) / (1024 * 1024), 1)
        except OSError:
            size_mb = 0.0
        videos.append({"name": filename, "path": full_path, "size_mb": size_mb})
    return videos


class LocalPlayerApp:
    """Interactive local video browser + player."""

    def __init__(self, folder: str = DOWNLOAD_DIR):
        self.folder = folder
        display(HTML(THEME_CSS))
        self._build_widgets()

    def _build_widgets(self):
        self.refresh_button = widgets.Button(description="🔄 Refresh List", button_style="info")
        self.status = widgets.HTML("")
        self.video_list = widgets.VBox([])
        self.player_output = widgets.Output()

        self.refresh_button.on_click(self._on_refresh)

        self.layout = widgets.VBox([
            widgets.HTML("<h2 class='ytstudio-header'>🎞️ Local Video Player</h2>"),
            widgets.HTML(
                f"<p style='color:#9aa0b4;font-size:12px;'>Scanning folder: <code>{self.folder}/</code></p>"
            ),
            self.refresh_button,
            self.status,
            self.video_list,
            self.player_output,
        ])
        self._on_refresh(None)

    def _on_refresh(self, _button):
        self.status.value = "<i style='color:#9aa0b4;'>Scanning downloads folder…</i>"
        self.video_list.children = []
        videos = list_downloaded_videos(self.folder)
        if not videos:
            self.status.value = (
                f"<span style='color:#ffb74d;'>No downloaded videos found in '{self.folder}/'. "
                f"Download something first, then click Refresh.</span>"
            )
            return
        self.status.value = f"<span style='color:#81c784;'>Found {len(videos)} downloaded video(s).</span>"
        self.video_list.children = [self._build_video_row(v) for v in videos]

    def _build_video_row(self, video: dict) -> widgets.HBox:
        label = widgets.HTML(
            f"<div class='ytstudio-title'>🎬 {video['name']}</div>"
            f"<div class='ytstudio-meta'>💾 {video['size_mb']} MB</div>"
        )
        play_button = widgets.Button(
            description="▶ Play", button_style="success", layout=widgets.Layout(width="100px")
        )
        play_button.on_click(lambda _btn, v=video: self._play_video(v))
        row = widgets.HBox(
            [label, play_button],
            layout=widgets.Layout(justify_content="space-between", align_items="center", width="600px"),
        )
        row.add_class("ytstudio-card")
        return row

    def _play_video(self, video: dict):
        with self.player_output:
            clear_output(wait=True)
            if not os.path.exists(video["path"]):
                render_playback_error("File no longer exists. Click Refresh to update the list.")
                return
            try:
                server = MediaServer.get_instance(self.folder)
                stream_url = server.url_for(video["path"])
                render_plyr_player(stream_url, title=video["name"])
            except Exception as exc:
                render_playback_error(f"Could not play this file: {exc}", video["path"])

    def display(self):
        display(self.layout)
