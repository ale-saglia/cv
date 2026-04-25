"""Local HTTP server for site preview. Run after build_pages_site.py."""

import http.server
import os
import threading
import webbrowser
from pathlib import Path

PORT = 8080
SITE_DIR = Path(__file__).resolve().parents[1] / "site"

os.chdir(SITE_DIR)

timer = threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}"))
timer.start()

print(f"Serving {SITE_DIR} at http://localhost:{PORT}  (Ctrl+C to stop)")
http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=PORT, bind="")
