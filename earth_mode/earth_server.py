#!/usr/bin/env python3
"""
earth_mode/earth_server.py
Local static file server for ULTRON Earth Mode with aggressive no-cache
headers, so the browser always fetches the latest earth.html instead of
serving a stale cached copy. Also serves /earth_cmd for the voice bridge.
"""
import http.server
import socketserver
import os
import json

PORT = 8765
DIR = os.path.dirname(os.path.abspath(__file__))
DATA_CANDIDATES = [
    os.path.join(os.path.dirname(DIR), "data", "earth_cmd.json"),
    os.path.join(DIR, "data", "earth_cmd.json"),
]


def find_data_file():
    for p in DATA_CANDIDATES:
        if os.path.exists(p):
            return p
    return DATA_CANDIDATES[0]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        if self.path.startswith("/earth_cmd"):
            data_file = find_data_file()
            try:
                if os.path.exists(data_file):
                    with open(data_file, "r", encoding="utf-8") as f:
                        content = f.read()
                else:
                    content = json.dumps({"cmd": None, "ts": 0})
            except Exception:
                content = json.dumps({"cmd": None, "ts": 0})
            body = content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"[EARTH SERVER] Serving {DIR} on http://localhost:{PORT} (no-cache headers ON)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
