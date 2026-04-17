#!/usr/bin/env python3
"""
Label-Selector-Lab: Pod App

A simple HTTP server that returns its own identity:
pod name, namespace, and the labels injected via environment variables.
This makes it easy to see WHICH pod responds when queries are filtered by label.
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Labels are injected from the Downward API via environment variables
POD_NAME      = os.environ.get("POD_NAME", "unknown")
NAMESPACE     = os.environ.get("NAMESPACE", "unknown")
LABEL_ENV     = os.environ.get("LABEL_ENV", "unknown")      # e.g. prod / dev
LABEL_TIER    = os.environ.get("LABEL_TIER", "unknown")     # e.g. frontend / backend
LABEL_TEAM    = os.environ.get("LABEL_TEAM", "unknown")     # e.g. alpha / beta
PORT          = int(os.environ.get("PORT", 8080))


class PodInfoHandler(BaseHTTPRequestHandler):
    """Handles incoming HTTP requests."""

    def log_message(self, format, *args):
        # Suppress default access logs for cleaner output
        pass

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_json(200, {
                "message": "Label-Selector-Lab pod is running!",
                "pod_name": POD_NAME,
                "namespace": NAMESPACE,
                "labels": {
                    "env":  LABEL_ENV,
                    "tier": LABEL_TIER,
                    "team": LABEL_TEAM,
                },
            })

        elif parsed.path == "/health":
            self._send_json(200, {"status": "healthy"})

        else:
            self._send_json(404, {"error": "not found"})

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    server = HTTPServer(("0.0.0.0", PORT), PodInfoHandler)
    print(f"[Label-Selector-Lab] Pod '{POD_NAME}' starting on port {PORT}")
    print(f"  namespace : {NAMESPACE}")
    print(f"  env       : {LABEL_ENV}")
    print(f"  tier      : {LABEL_TIER}")
    print(f"  team      : {LABEL_TEAM}")
    server.serve_forever()


if __name__ == "__main__":
    main()
