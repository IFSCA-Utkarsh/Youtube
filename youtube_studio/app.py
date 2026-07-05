"""
app.py
======
Main application layer: assembles the ipywidgets UI and wires it to the
engine modules. Three top-level tabs:

    1. 🔍 Search Videos     — keyword search -> select a video
    2. 📺 Browse a Channel  — search a channel -> Videos / Playlists / Shorts / Live
    3. ⬇️ Download & Play   — pick a quality, download, then play with Plyr

Selecting any video (from search, a channel tab, or a playlist) jumps to
"Download & Play", where the video is downloaded first and streamed back
from the local media server via a modern Plyr player — never through an
embedded YouTube iframe, which is what avoids "Error 153" entirely.
"""

from __future__ import annotations

import ipywidgets as widgets
from IPython.display import HTML, clear_output, display

from .channel_engine import ChannelEngine
from .config import CHANNEL_SECTIONS, THEME_CSS
from .download_engine import DownloadEngine
from .media_server import MediaServer
from .player import render_playback_error, render_plyr_player
from .search_engine import SearchEngine
from .ui_components import (
    build_channel_result_card,
    build_empty_state,
    build_playlist_card,
    build_video_card,
)

_SECTION_ICONS = {"videos": "🎬", "playlists": "📁", "shorts": "🔀", "live": "🔴"}
_SECTION_LABELS = {"videos": "Videos", "playlists": "Playlists", "shorts": "Shorts", "live": "Live"}


class YouTubeStudioApp:
    """Top-level application object. Call `.display()` to render it."""

    def __init__(self):
        self.search_engine = SearchEngine()
        self.channel_engine = ChannelEngine()
        self.download_engine = DownloadEngine()

        self.selected_channel: dict | None = None
        self.active_section = "videos"

        display(HTML(THEME_CSS))
        self._build_widgets()

    # ------------------------------------------------------------ build UI
    def _build_widgets(self):
        self._build_search_tab()
        self._build_channel_tab()
        self._build_download_tab()

        self.tabs = widgets.Tab(children=[self.search_tab, self.channel_tab, self.download_tab])
        for index, title in enumerate(["🔍 Search Videos", "📺 Browse Channel", "⬇️ Download & Play"]):
            self.tabs.set_title(index, title)

    # ---------------------------------------------------------- Tab 1: Search
    def _build_search_tab(self):
        self.search_box = widgets.Text(
            placeholder="Search videos… e.g. 'python tutorial'",
            layout=widgets.Layout(width="70%"),
        )
        self.search_button = widgets.Button(description="🔍 Search", button_style="info")
        self.search_status = widgets.HTML("")
        self.search_results = widgets.VBox([])

        self.search_button.on_click(self._on_search_click)
        self.search_box.on_submit(self._on_search_click)

        self.search_tab = widgets.VBox([
            widgets.HBox([self.search_box, self.search_button]),
            self.search_status,
            self.search_results,
        ])

    def _on_search_click(self, _widget):
        self.search_status.value = "<i style='color:#9aa0b4;'>Searching…</i>"
        self.search_results.children = []
        try:
            results = self.search_engine.search_videos(self.search_box.value, limit=8)
            if not results:
                self.search_status.value = "<span style='color:#ffb74d;'>No results found.</span>"
                return
            self.search_status.value = f"<span style='color:#81c784;'>Found {len(results)} videos.</span>"
            self.search_results.children = [build_video_card(v, self._render_download_panel) for v in results]
        except Exception as exc:
            self.search_status.value = f"<span style='color:#e57373;'>⚠️ {exc}</span>"

    # ---------------------------------------------------- Tab 2: Browse Channel
    def _build_channel_tab(self):
        self.channel_search_box = widgets.Text(
            placeholder="Search channels… e.g. 'freeCodeCamp'",
            layout=widgets.Layout(width="70%"),
        )
        self.channel_search_button = widgets.Button(description="🔍 Search Channels", button_style="info")
        self.channel_status = widgets.HTML("")
        self.channel_results = widgets.VBox([])

        self.channel_search_button.on_click(self._on_channel_search_click)
        self.channel_search_box.on_submit(self._on_channel_search_click)

        # Section navigation (Videos / Playlists / Shorts / Live), populated
        # once a channel has been selected.
        self.section_header = widgets.HTML("")
        self.section_buttons = {}
        section_button_row = []
        for section in CHANNEL_SECTIONS:
            btn = widgets.Button(
                description=f"{_SECTION_ICONS[section]} {_SECTION_LABELS[section]}",
                button_style="primary" if section == "videos" else "",
            )
            btn.on_click(lambda _b, s=section: self._load_channel_section(s))
            self.section_buttons[section] = btn
            section_button_row.append(btn)

        self.section_status = widgets.HTML("")
        self.section_results = widgets.VBox([])
        self.channel_section_area = widgets.VBox([])  # hidden until a channel is picked

        self._section_button_row = widgets.HBox(section_button_row)

        self.channel_tab = widgets.VBox([
            widgets.HBox([self.channel_search_box, self.channel_search_button]),
            self.channel_status,
            self.channel_results,
            self.channel_section_area,
        ])

    def _on_channel_search_click(self, _widget):
        self.channel_status.value = "<i style='color:#9aa0b4;'>Searching channels…</i>"
        self.channel_results.children = []
        self.channel_section_area.children = []
        try:
            results = self.channel_engine.search_channels(self.channel_search_box.value, limit=6)
            if not results:
                self.channel_status.value = "<span style='color:#ffb74d;'>No channels found.</span>"
                return
            self.channel_status.value = f"<span style='color:#81c784;'>Found {len(results)} channels.</span>"
            self.channel_results.children = [
                build_channel_result_card(c, self._on_channel_selected) for c in results
            ]
        except Exception as exc:
            self.channel_status.value = f"<span style='color:#e57373;'>⚠️ {exc}</span>"

    def _on_channel_selected(self, channel: dict):
        self.selected_channel = channel
        self.active_section = "videos"
        for section, btn in self.section_buttons.items():
            btn.button_style = "primary" if section == "videos" else ""

        self.section_header.value = (
            f"<h4 style='color:#f5f5f7;margin:12px 0 4px 0;'>📺 {channel['title']}</h4>"
        )
        self.section_status.value = ""
        self.section_results.children = []
        self.channel_section_area.children = [
            self.section_header,
            self._section_button_row,
            self.section_status,
            self.section_results,
        ]
        self._load_channel_section("videos")

    def _load_channel_section(self, section: str):
        if not self.selected_channel:
            return

        self.active_section = section
        for s, btn in self.section_buttons.items():
            btn.button_style = "primary" if s == section else ""

        label = _SECTION_LABELS[section]
        self.section_status.value = f"<i style='color:#9aa0b4;'>Loading {label}…</i>"
        self.section_results.children = []
        try:
            items = self.channel_engine.get_section(self.selected_channel["url"], section, limit=12)
            if not items:
                self.section_status.value = f"<span style='color:#ffb74d;'>No {label.lower()} found for this channel.</span>"
                return
            self.section_status.value = f"<span style='color:#81c784;'>Showing {len(items)} {label.lower()}.</span>"
            if section == "playlists":
                self.section_results.children = [
                    build_playlist_card(p, self._on_playlist_selected) for p in items
                ]
            else:
                self.section_results.children = [
                    build_video_card(v, self._render_download_panel) for v in items
                ]
        except Exception as exc:
            self.section_status.value = f"<span style='color:#e57373;'>⚠️ {exc}</span>"

    def _on_playlist_selected(self, playlist: dict):
        self.section_status.value = "<i style='color:#9aa0b4;'>Loading playlist videos…</i>"
        self.section_results.children = []
        try:
            videos = self.channel_engine.get_playlist_videos(playlist["url"], limit=12)
            if not videos:
                self.section_status.value = "<span style='color:#ffb74d;'>This playlist appears to be empty.</span>"
                return
            self.section_status.value = (
                f"<span style='color:#81c784;'>Showing {len(videos)} videos from "
                f"“{playlist['title']}”.</span>"
            )
            self.section_results.children = [build_video_card(v, self._render_download_panel) for v in videos]
        except Exception as exc:
            self.section_status.value = f"<span style='color:#e57373;'>⚠️ {exc}</span>"

    # ------------------------------------------------- Tab 3: Download & Play
    def _build_download_tab(self):
        self.download_output = widgets.Output()
        with self.download_output:
            display(build_empty_state(
                "Select a video from Search or a Channel to download and play it here."
            ))
        self.download_tab = widgets.VBox([self.download_output])

    @staticmethod
    def _make_progress_hook(progress_bar, status_html):
        """Build a yt-dlp progress_hook that live-updates a progress bar widget."""

        def hook(d):
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes", 0)
                if total:
                    percent = downloaded / total * 100
                    progress_bar.value = percent
                    status_html.value = f"<span style='color:#9aa0b4;'>Downloading… {percent:.1f}%</span>"
                else:
                    status_html.value = "<span style='color:#9aa0b4;'>Downloading…</span>"
            elif d.get("status") == "finished":
                progress_bar.value = 100
                status_html.value = "<span style='color:#9aa0b4;'>Finalizing (merging audio/video)…</span>"

        return hook

    def _render_download_panel(self, video: dict):
        """Populate 'Download & Play' for the selected video and jump to it."""
        self.tabs.selected_index = 2

        with self.download_output:
            clear_output(wait=True)

            from .utils import fetch_image_bytes
            thumb_bytes = fetch_image_bytes(video["thumbnail"])
            if thumb_bytes:
                display(widgets.Image(value=thumb_bytes, format="jpg", width=320, height=180))
            display(HTML(
                f"<div class='ytstudio-title' style='font-size:16px;margin-top:8px;'>{video['title']}</div>"
                f"<div class='ytstudio-meta'>📺 {video['channel']} &nbsp;|&nbsp; ⏱ {video['duration']}</div>"
            ))

            quality_status = widgets.HTML("<i style='color:#9aa0b4;'>Fetching available qualities…</i>")
            display(quality_status)

            try:
                qualities = self.download_engine.get_available_qualities(video["id"])
            except Exception as exc:
                quality_status.value = f"<span style='color:#e57373;'>⚠️ {exc}</span>"
                return

            quality_status.value = f"<span style='color:#81c784;'>Found {len(qualities)} quality option(s).</span>"
            quality_dropdown = widgets.Dropdown(
                options=[(f"{h}p", h) for h in qualities],
                description="Quality:",
                style={"description_width": "initial"},
            )
            download_button = widgets.Button(description="⬇️ Download", button_style="success")
            progress_bar = widgets.FloatProgress(
                value=0, min=0, max=100, description="Progress:",
                layout=widgets.Layout(width="400px", visibility="hidden"),
            )
            download_status = widgets.HTML("")
            play_area = widgets.Output()

            def _on_download_click(_btn, v=video):
                download_button.disabled = True
                progress_bar.value = 0
                progress_bar.layout.visibility = "visible"
                download_status.value = "<i style='color:#9aa0b4;'>Starting download…</i>"
                hook = self._make_progress_hook(progress_bar, download_status)
                try:
                    result = self.download_engine.download_video(
                        v["id"], quality_dropdown.value, progress_hook=hook
                    )
                except Exception as exc:
                    download_status.value = f"<span style='color:#e57373;'>⚠️ {exc}</span>"
                    download_button.disabled = False
                    return

                download_status.value = (
                    f"<span style='color:#81c784;'>✅ Downloaded ({result['size_mb']} MB). "
                    f"Starting player…</span>"
                )
                with play_area:
                    clear_output(wait=True)
                    try:
                        server = MediaServer.get_instance()
                        stream_url = server.url_for(result["path"])
                        render_plyr_player(stream_url, title=v["title"])
                    except Exception as exc:
                        render_playback_error(f"Could not start the player: {exc}", result["path"])

                    save_button = widgets.Button(description="💾 Save to My Computer")

                    def _on_save_click(_b, path=result["path"]):
                        try:
                            from google.colab import files as colab_files
                            colab_files.download(path)
                        except ImportError:
                            print("google.colab.files is only available inside Google Colab.")
                        except Exception as exc2:
                            print(f"Could not trigger download: {exc2}")

                    save_button.on_click(_on_save_click)
                    display(save_button)

                download_button.disabled = False

            download_button.on_click(_on_download_click)
            display(widgets.HBox([quality_dropdown, download_button]))
            display(progress_bar)
            display(download_status)
            display(play_area)

    # ------------------------------------------------------------ public
    def display(self):
        display(HTML("<h2 class='ytstudio-header'>🎬 YouTube Studio — Download & Play Edition</h2>"))
        display(self.tabs)
