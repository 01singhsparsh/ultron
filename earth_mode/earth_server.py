#!/usr/bin/env python3
"""
earth_mode/earth_server.py
Local static file server for ULTRON Earth Mode.
 - aggressive no-cache headers so the browser always gets the latest earth.html
 - /earth_cmd endpoint = JSON bridge (reads data/earth_cmd.json)
 - start_server()  -> used by earth_mode.py: starts the server in a background
                      thread and returns immediately (safe to call twice)
 - run directly (py -3.11 earth_server.py) -> blocks and serves forever
"""
import http.server
import socketserver
import threading
import os
import json

PORT = 8765
HOST = "127.0.0.1"
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
                    with open(data_file, "r", encoding="utf-8-sig") as f:
                        content = f.read()
                    json.loads(content)  # make sure it is valid JSON
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


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


_server = None


def start_server():
    """Start the Earth Mode web server in a background thread (idempotent)."""
    global _server
    if _server is not None:
        return _server
    try:
        _server = _Server((HOST, PORT), Handler)
    except OSError as e:
        # Port already taken -> most likely an earlier Earth server is still running
        print(f"[EARTH SERVER] Port {PORT} busy ({e}); assuming a server is already running.")
        return None
    t = threading.Thread(target=_server.serve_forever, daemon=True)
    t.start()
    print(f"[EARTH SERVER] Serving {DIR} on http://localhost:{PORT} (no-cache ON)")
    return _server


if __name__ == "__main__":
    srv = start_server()
    if srv is None:
        print("[EARTH SERVER] Nothing to do - a server is already running on this port.")
    else:
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
