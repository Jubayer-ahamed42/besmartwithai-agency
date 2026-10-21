"""
Be Smart With AI - Agency Web Server & REST API
Author: Jubayer Ahamed
Runs a local HTTP server with static file serving and JSON API for Engineering Articles.

Usage:
    python server.py [port]
Example:
    python server.py 8080
"""

import http.server
import socketserver
import os
import json
import urllib.parse
import sys

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load articles data
ARTICLES_FILE = os.path.join(BASE_DIR, 'insights', 'articles.json')
if not os.path.exists(ARTICLES_FILE):
    scratch_json = os.path.join(r'C:\Users\ASSDI\.gemini\antigravity\brain\ceb2303f-fae3-44e0-866f-841964bdaad8\scratch', 'articles_perfect.json')
    if os.path.exists(scratch_json):
        with open(scratch_json, 'r', encoding='utf-8') as f:
            articles_db = json.load(f)
    else:
        articles_db = {}
else:
    with open(ARTICLES_FILE, 'r', encoding='utf-8') as f:
        articles_db = json.load(f)

class AgencyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. REST API: Get all articles
        if path == '/api/articles':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            summary = [
                {
                    'id': k,
                    'slug': v['slug'],
                    'category': v['category'],
                    'readTime': v['readTime'],
                    'date': v.get('date', 'October 2026'),
                    'title': v['title'],
                    'subtitle': v['subtitle'],
                    'author': v['author'],
                    'url': f'/insights/{v["slug"]}.html'
                }
                for k, v in articles_db.items()
            ]
            self.wfile.write(json.dumps(summary, indent=2, ensure_ascii=False).encode('utf-8'))
            return

        # 2. REST API: Get single article by ID or slug
        if path.startswith('/api/articles/'):
            key = path.replace('/api/articles/', '').strip('/')
            article = articles_db.get(key)
            if not article:
                for k, v in articles_db.items():
                    if v.get('slug') == key:
                        article = v
                        break
            
            if article:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(article, indent=2, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Article not found'}).encode('utf-8'))
            return

        # 3. Clean URL routing for insights without .html extension
        if path.startswith('/insights/'):
            subpath = path.replace('/insights/', '').strip('/')
            possible_html = os.path.join(BASE_DIR, 'insights', f'{subpath}.html')
            if os.path.exists(possible_html):
                self.path = f'/insights/{subpath}.html'

        super().do_GET()

def run_server():
    os.makedirs(os.path.join(BASE_DIR, 'insights'), exist_ok=True)
    with open(os.path.join(BASE_DIR, 'insights', 'articles.json'), 'w', encoding='utf-8') as f:
        json.dump(articles_db, f, indent=2, ensure_ascii=False)

    with socketserver.TCPServer(("", PORT), AgencyRequestHandler) as httpd:
        print("=======================================================")
        print(f"[SERVER] Be Smart With AI - Backend Server Running")
        print(f"[URL] http://localhost:{PORT}")
        print(f"[API] http://localhost:{PORT}/api/articles")
        print("Press Ctrl+C to stop the server")
        print("=======================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == '__main__':
    run_server()
