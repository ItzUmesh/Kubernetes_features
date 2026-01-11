import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import request, error

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8080"))

# Environment-based configuration
API_KEY = os.getenv("API_KEY", "")
UPSTREAM_URL = os.getenv("UPSTREAM_URL", "")


def fetch_upstream(path: str) -> tuple[int, bytes]:
    """Fetch from upstream and return (status, body)."""
    if not UPSTREAM_URL:
        return 500, b"Missing upstream URL"
    url = f"{UPSTREAM_URL}{path}"
    req = request.Request(url, headers={"X-API-KEY": API_KEY}) if API_KEY else request.Request(url)
    try:
        with request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read()
    except error.HTTPError as exc:
        return exc.code, exc.read()
    except Exception as exc:  # noqa: BLE001 broad for demo simplicity
        return 502, f"Upstream error: {exc}".encode()


class ProxyHandler(BaseHTTPRequestHandler):
    def _write_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth_failed(self) -> None:
        self._write_json(401, {"error": "missing or invalid API key"})

    def _check_key(self) -> bool:
        provided = self.headers.get("X-API-KEY", "")
        return bool(API_KEY) and provided == API_KEY

    def do_GET(self) -> None:  # noqa: N802 naming from BaseHTTPRequestHandler
        if not self._check_key():
            self._auth_failed()
            return
        status, body = fetch_upstream(self.path)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 naming from BaseHTTPRequestHandler
        if not self._check_key():
            self._auth_failed()
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length) if length else b""
        status, body = self._forward_post(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _forward_post(self, payload: bytes) -> tuple[int, bytes]:
        if not UPSTREAM_URL:
            return 500, b"Missing upstream URL"
        url = f"{UPSTREAM_URL}{self.path}"
        req = request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "X-API-KEY": API_KEY} if API_KEY else {"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=5) as resp:
                return resp.status, resp.read()
        except error.HTTPError as exc:
            return exc.code, exc.read()
        except Exception as exc:  # noqa: BLE001 broad for demo simplicity
            return 502, f"Upstream error: {exc}".encode()

    def log_message(self, format: str, *args) -> None:  # noqa: A003 shadow built-in
        # Quiet the default stdout logging; uncomment for debug
        return


def run() -> None:
    server = HTTPServer((HOST, PORT), ProxyHandler)
    print(f"Secure API Proxy running on port {PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
