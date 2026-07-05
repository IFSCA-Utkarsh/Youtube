"""
media_server.py
================
A tiny local HTTP server that streams files out of DOWNLOAD_DIR with proper
HTTP Range support (required for video seeking and for the browser to start
playback before the whole file is loaded).

Why this exists
---------------
The original implementation played videos by base64-encoding the entire
file into the notebook's HTML output (`IPython.display.Video(embed=True)`).
That is slow to render, bloats notebook output size, and cannot seek until
fully loaded. Serving the file over real HTTP with Range support lets the
modern Plyr-based player (see player.py) start playback almost instantly
and seek anywhere in the file, exactly like a normal streaming video.

Colab note
----------
Google Colab sandboxes localhost, so a plain "http://127.0.0.1:PORT/..."
URL is not reachable from the notebook's browser tab. Colab provides
`google.colab.output.eval_js("google.colab.kernel.proxyPort(PORT)")` to
obtain a browser-reachable proxy URL for a local port; this module uses
that automatically when running inside Colab, and falls back to a plain
localhost URL otherwise (e.g. plain Jupyter).
"""

from __future__ import annotations

import http.server
import os
import re
import socket
import threading
import urllib.parse

from .config import DOWNLOAD_DIR, MEDIA_SERVER_HOST, MEDIA_SERVER_PORT_RANGE
from .utils import in_colab

_RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


class _RangeRequestHandler(http.server.BaseHTTPRequestHandler):
    """Minimal HTTP handler that serves files from `directory` with Range support."""

    directory: str = DOWNLOAD_DIR

    # Silence per-request console spam.
    def log_message(self, format, *args):  # noqa: A002 (shadowing builtin `format`)
        pass

    def _resolve_path(self):
        rel = urllib.parse.unquote(self.path.lstrip("/").split("?")[0])
        full = os.path.abspath(os.path.join(self.directory, rel))
        root = os.path.abspath(self.directory)
        if not full.startswith(root):
            return None
        return full

    def _serve(self, send_body: bool):
        path = self._resolve_path()
        if not path or not os.path.isfile(path):
            self.send_error(404, "File not found")
            return

        file_size = os.path.getsize(path)
        start, end = 0, file_size - 1
        status = 200

        range_header = self.headers.get("Range")
        if range_header:
            match = _RANGE_RE.match(range_header)
            if match:
                g_start, g_end = match.groups()
                if g_start:
                    start = int(g_start)
                if g_end:
                    end = int(g_end)
                end = min(end, file_size - 1)
                status = 206

        length = max(0, end - start + 1)
        import mimetypes
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.end_headers()

        if not send_body:
            return

        chunk_size = 256 * 1024
        with open(path, "rb") as handle:
            handle.seek(start)
            remaining = length
            while remaining > 0:
                data = handle.read(min(chunk_size, remaining))
                if not data:
                    break
                try:
                    self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError):
                    break
                remaining -= len(data)

    def do_GET(self):  # noqa: N802 (http.server naming convention)
        self._serve(send_body=True)

    def do_HEAD(self):  # noqa: N802
        self._serve(send_body=False)


def _find_free_port(host: str, port_range) -> int:
    for port in range(*port_range):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, port)) != 0:
                return port
    raise RuntimeError("No free port found for the media server.")


class MediaServer:
    """Singleton-style background HTTP server serving DOWNLOAD_DIR."""

    _instance: "MediaServer | None" = None

    def __init__(self, directory: str = DOWNLOAD_DIR):
        self.directory = directory
        os.makedirs(self.directory, exist_ok=True)
        self.port = _find_free_port(MEDIA_SERVER_HOST, MEDIA_SERVER_PORT_RANGE)
        _RangeRequestHandler.directory = self.directory
        self._httpd = http.server.ThreadingHTTPServer((MEDIA_SERVER_HOST, self.port), _RangeRequestHandler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    @classmethod
    def get_instance(cls, directory: str = DOWNLOAD_DIR) -> "MediaServer":
        if cls._instance is None:
            cls._instance = cls(directory)
        return cls._instance

    def url_for(self, filename: str) -> str:
        """Return a browser-reachable URL for `filename` inside DOWNLOAD_DIR."""
        quoted = urllib.parse.quote(os.path.basename(filename))
        if in_colab():
            from google.colab.output import eval_js  # type: ignore
            proxy_base = eval_js(f"google.colab.kernel.proxyPort({self.port})")
            return proxy_base.rstrip("/") + "/" + quoted
        return f"http://{MEDIA_SERVER_HOST}:{self.port}/{quoted}"

    def shutdown(self):
        self._httpd.shutdown()
