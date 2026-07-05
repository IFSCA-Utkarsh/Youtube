"""
ui_components.py
==================
Reusable ipywidgets "card" builders for videos, channels, and playlists.
Pure presentation layer — no yt-dlp calls happen here.
"""

from __future__ import annotations

import ipywidgets as widgets

from .utils import fetch_image_bytes


def build_video_card(video: dict, on_select) -> widgets.HBox:
    """One clickable video card: thumbnail + info + Select button."""
    img_bytes = fetch_image_bytes(video["thumbnail"])
    if img_bytes:
        thumbnail = widgets.Image(value=img_bytes, format="jpg", width=160, height=90)
    else:
        thumbnail = widgets.HTML(
            "<div style='width:160px;height:90px;background:#333;border-radius:8px;'></div>"
        )

    live_badge = "<span class='ytstudio-badge' style='color:#e57373;'>LIVE</span>" if video.get("is_live") else ""
    info_html = widgets.HTML(
        f"<div class='ytstudio-title'>{live_badge}{video['title'][:70]}</div>"
        f"<div class='ytstudio-meta'>📺 {video['channel']}</div>"
        f"<div class='ytstudio-meta'>⏱ {video['duration']} &nbsp;|&nbsp; 👁 {video['views']}</div>"
    )
    select_button = widgets.Button(
        description="⬇️ Select", button_style="success",
        layout=widgets.Layout(width="110px", margin="6px 0 0 0"),
    )
    select_button.on_click(lambda _btn, v=video: on_select(v))

    card = widgets.HBox([
        thumbnail,
        widgets.VBox([info_html, select_button], layout=widgets.Layout(margin="0 0 0 14px")),
    ])
    card.add_class("ytstudio-card")
    return card


def build_channel_result_card(channel: dict, on_browse) -> widgets.HBox:
    """One channel search-result card: avatar + info + Browse button."""
    img_bytes = fetch_image_bytes(channel["thumbnail"])
    if img_bytes:
        avatar = widgets.Image(value=img_bytes, format="jpg", width=80, height=80)
    else:
        avatar = widgets.HTML(
            "<div style='width:80px;height:80px;background:#333;border-radius:50%;'></div>"
        )

    info_html = widgets.HTML(
        f"<div class='ytstudio-title'>{channel['title']}</div>"
        f"<div class='ytstudio-meta'>👥 {channel['subscribers']}</div>"
        f"<div class='ytstudio-meta'>{(channel['description'] or '')[:110]}</div>"
    )
    browse_button = widgets.Button(
        description="📂 Browse Channel", button_style="info",
        layout=widgets.Layout(width="140px", margin="6px 0 0 0"),
    )
    browse_button.on_click(lambda _btn, c=channel: on_browse(c))

    card = widgets.HBox([
        avatar,
        widgets.VBox([info_html, browse_button], layout=widgets.Layout(margin="0 0 0 14px")),
    ])
    card.add_class("ytstudio-card")
    return card


def build_playlist_card(playlist: dict, on_view) -> widgets.HBox:
    """One playlist card: icon + title + View Videos button."""
    icon = widgets.HTML(
        "<div style='width:80px;height:80px;background:#2b2f45;border-radius:10px;"
        "display:flex;align-items:center;justify-content:center;font-size:28px;'>📁</div>"
    )
    count = playlist.get("video_count")
    count_html = f"<div class='ytstudio-meta'>{count} videos</div>" if count else ""
    info_html = widgets.HTML(f"<div class='ytstudio-title'>{playlist['title']}</div>{count_html}")
    view_button = widgets.Button(
        description="▶ View Videos", button_style="warning",
        layout=widgets.Layout(width="130px", margin="6px 0 0 0"),
    )
    view_button.on_click(lambda _btn, p=playlist: on_view(p))

    card = widgets.HBox([
        icon,
        widgets.VBox([info_html, view_button], layout=widgets.Layout(margin="0 0 0 14px")),
    ])
    card.add_class("ytstudio-card")
    return card


def build_empty_state(message: str) -> widgets.HTML:
    return widgets.HTML(f"<p style='color:#9aa0b4;'>{message}</p>")
