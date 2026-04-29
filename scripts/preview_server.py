"""Local development server that simulates GitHub Pages 404 behavior."""

import http.server
import socketserver
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT_DIR / "_site"


class GitHubPagesHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler that serves 404.html on 404 errors, like GitHub Pages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE_DIR), **kwargs)

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            error_file = SITE_DIR / "404.html"
            if error_file.exists():
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                with open(error_file, "rb") as f:
                    self.wfile.write(f.read())
                return
        super().send_error(code, message, explain)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    
    # Allow address reuse to avoid "Address already in use" after restart
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", port), GitHubPagesHandler) as httpd:
        print(f"Preview server running at http://localhost:{port}")
        print("Serving directory:", SITE_DIR)
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")


if __name__ == "__main__":
    main()
