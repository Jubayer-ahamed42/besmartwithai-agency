import os
import sys
import time
import urllib.request
import threading
import unittest
import socketserver
import http.server

# Import AgencyRequestHandler from server.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import AgencyRequestHandler

TEST_PORT = 8991

class TestHTTPServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = socketserver.TCPServer(("127.0.0.1", TEST_PORT), AgencyRequestHandler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_root_index_html(self):
        url = f"http://127.0.0.1:{TEST_PORT}/"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/html", resp.headers.get("Content-Type", ""))
            body = resp.read().decode('utf-8')
            self.assertIn("Jubayer Ahamed", body)

    def test_webp_asset_mime(self):
        url = f"http://127.0.0.1:{TEST_PORT}/assets/jubayer.webp"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get("Content-Type"), "image/webp")
            data = resp.read()
            self.assertGreater(len(data), 100000)

    def test_jpg_asset_mime(self):
        url = f"http://127.0.0.1:{TEST_PORT}/assets/jubayer.jpg"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get("Content-Type"), "image/jpeg")
            data = resp.read()
            self.assertGreater(len(data), 100000)

if __name__ == '__main__':
    unittest.main()
