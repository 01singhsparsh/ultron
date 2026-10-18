#!/usr/bin/env python3
"""
earth_server.py
Local HTTP server for ULTRON Earth Mode.
Serves earth.html on localhost:8765 (matches MapTiler key restriction).
Also serves /earth_cmd endpoint for Python-browser bridge.
"""
import os, sys, json, time, threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EARTH_DIR  = os.path.join(BASE_DIR, "earth_mode")
CMD_FILE   = os.path.join(BASE_DIR, "data", "earth_cmd.json")
PORT       = 8765
_server    = None
_thread    = None

class EarthHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=EARTH_DIR, **kwargs)

    def do_GET(self):
        # Bridge endpoint — return current command
        if self.path.startswith("/earth_cmd"):
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("Cache-Control","no-store")
            self.end_headers()
            try:
                if os.path.exists(CMD_FILE):
                    with open(CMD_FILE) as f:
                        data = f.read()
                    self.wfile.write(data.encode())
                else:
                    self.wfile.write(b"{}")
            except:
                self.wfile.write(b"{}")
            return
        # Serve static files
        super().do_GET()

    def log_message(self, format, *args):
        pass  # Silent

def start_server():
    global _server, _thread
    if _server: return
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    _server = HTTPServer(("localhost", PORT), EarthHandler)
    _thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _thread.start()
    print(f"[EARTH SERVER] Running on http://localhost:{PORT}")

def stop_server():
    global _server
    if _server:
        _server.shutdown()
        _server = None

def get_url():
    return f"http://localhost:{PORT}/earth.html"

if __name__ == "__main__":
    start_server()
    print(f"Open: http://localhost:{PORT}/earth.html")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        stop_server()
