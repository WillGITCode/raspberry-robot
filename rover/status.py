"""Read-only live status over HTTP, on a daemon thread. The tick loop only swaps a snapshot.

GET /        the status page (rover/static/index.html)
GET /state   the latest snapshot as JSON
GET /events  the snapshot as server-sent events, 10 a second

There is no control endpoint: nothing here can move the robot.
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 8080
PAGE = Path(__file__).with_name("static") / "index.html"
STREAM_PERIOD_S = 0.1


class StatusServer:
    def __init__(self, host="0.0.0.0", port=PORT, page=PAGE):
        self.snapshot = {}
        self.page = page
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # keep the journal for the robot's own events
                pass

            def do_GET(self):
                path = self.path.split("?")[0]
                if path == "/":
                    self._send(200, "text/html; charset=utf-8", server.page.read_bytes())
                elif path == "/state":
                    self._send(200, "application/json", json.dumps(server.snapshot).encode())
                elif path == "/events":
                    self._stream()
                else:
                    self._send(404, "text/plain", b"not found\n")

            def _send(self, code, ctype, body):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def _stream(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                try:
                    while True:
                        self.wfile.write(b"data: " + json.dumps(server.snapshot).encode() + b"\n\n")
                        self.wfile.flush()
                        time.sleep(STREAM_PERIOD_S)
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass

        self.httpd = ThreadingHTTPServer((host, port), Handler)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True, name="status")
        self.thread.start()

    def publish(self, snapshot):
        self.snapshot = snapshot  # one reference swap: readers see the old or the new, never half

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()
