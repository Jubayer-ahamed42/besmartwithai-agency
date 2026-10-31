"""
Be Smart With AI - Agency Web Server
Author: Jubayer Ahamed
Runs a local HTTP server with static file serving and clean URL routing.

Usage:
    python server.py [port]
Example:
    python server.py 8080
"""

import http.server
import socketserver
import os
import urllib.parse
import sys
import mimetypes

mimetypes.add_type('image/webp', '.webp')

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def get_port():
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        return int(sys.argv[1])
    return 8080

PORT = get_port()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class AgencyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Clean URL support: e.g. /page -> /page.html if page.html exists
        clean_path = path.strip('/')
        if clean_path and not os.path.splitext(clean_path)[1]:
            possible_html = os.path.join(BASE_DIR, f"{clean_path}.html")
            if os.path.isfile(possible_html):
                self.path = f"/{clean_path}.html"

        super().do_GET()


def run_server():
    with socketserver.TCPServer(("", PORT), AgencyRequestHandler) as httpd:
        print("=======================================================")
        print(f"[SERVER] Be Smart With AI - Agency Web Server Running")
        print(f"[URL] http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server")
        print("=======================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")


if __name__ == '__main__':
    run_server()
