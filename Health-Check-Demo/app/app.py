#!/usr/bin/env python3
"""
Health Check Demo App

A simple Python HTTP server with a /health endpoint that can be toggled to fail,
triggering Kubernetes liveness probe restarts.
"""

import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse


# Global health state (defaults to healthy)
health_state = {"healthy": True}


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the health check app."""

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/':
            self.handle_index()
        elif path == '/health':
            self.handle_health()
        elif path == '/status':
            self.handle_status()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({"error": "Not found"})
            self.wfile.write(response.encode())

    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/toggle-health':
            self.handle_toggle_health()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({"error": "Not found"})
            self.wfile.write(response.encode())

    def handle_index(self):
        """GET / - Return basic app info."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {
            "app": "Health-Check-Demo",
            "version": "1.0",
            "status": "running",
            "hostname": os.getenv('HOSTNAME', 'unknown')
        }
        self.wfile.write(json.dumps(response).encode())

    def handle_health(self):
        """GET /health - Liveness probe endpoint."""
        if health_state["healthy"]:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({"status": "healthy"})
            self.wfile.write(response.encode())
        else:
            self.send_response(503)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({"status": "unhealthy"})
            self.wfile.write(response.encode())

    def handle_status(self):
        """GET /status - Return detailed health status."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {
            "healthy": health_state["healthy"],
            "state": "healthy" if health_state["healthy"] else "unhealthy",
            "message": "App is running normally" if health_state["healthy"] else "App is in unhealthy state"
        }
        self.wfile.write(json.dumps(response).encode())

    def handle_toggle_health(self):
        """POST /toggle-health - Toggle health state."""
        health_state["healthy"] = not health_state["healthy"]
        new_state = "healthy" if health_state["healthy"] else "unhealthy"
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {
            "message": f"Health toggled to {new_state}",
            "current_state": new_state
        }
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_server():
    """Start the HTTP server."""
    port = int(os.getenv('PORT', 5000))
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    print(f"Server running on port {port}...")
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
