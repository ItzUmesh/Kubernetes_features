#!/usr/bin/env python3
"""
Dynamic Theme App

A simple Python web app that reads a background color from a ConfigMap.
The color is loaded from a file mounted in the pod (/config/theme.conf).
This demonstrates how Kubernetes ConfigMaps decouple configuration from code.
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse


# Path to the ConfigMap file mounted in the pod
CONFIG_FILE = '/config/theme.conf'


def load_theme_config():
    """Load theme configuration from the mounted ConfigMap file."""
    default_config = {
        "background_color": "#141c22",  # Blue
        "title": "Dynamic Theme App",
        "theme_name": "Blue (default)"
    }
    
    # Try to read from mounted ConfigMap
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                file_content = f.read().strip()
                # Parse the config file (simple key=value format)
                config = {}
                for line in file_content.split('\n'):
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
                
                # Merge with defaults
                result = default_config.copy()
                result.update(config)
                return result
        except Exception as e:
            print(f"Error reading config: {e}, using defaults")
            return default_config
    else:
        # ConfigMap not mounted yet, use defaults
        return default_config


class ThemeHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the theme app."""

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/':
            self.handle_home()
        elif path == '/config':
            self.handle_config()
        elif path == '/health':
            self.handle_health()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({"error": "Not found"})
            self.wfile.write(response.encode())

    def handle_home(self):
        """GET / - Serve the HTML page with dynamic theme."""
        theme = load_theme_config()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{theme['title']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            background-color: {theme['background_color']};
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            color: white;
            transition: background-color 0.5s ease;
        }}
        
        .container {{
            text-align: center;
            background: rgba(0, 0, 0, 0.2);
            padding: 40px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 20px;
        }}
        
        .theme-info {{
            font-size: 1.2em;
            margin: 20px 0;
        }}
        
        .config-details {{
            background: rgba(0, 0, 0, 0.3);
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
            text-align: left;
            font-family: monospace;
            font-size: 0.9em;
        }}
        
        .label {{
            font-weight: bold;
            margin-top: 10px;
        }}
        
        .info-box {{
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            border-left: 4px solid rgba(255, 255, 255, 0.5);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{theme['title']}</h1>
        
        <div class="theme-info">
            <p>Current Theme: <strong>{theme['theme_name']}</strong></p>
            <p>Background Color: <strong>{theme['background_color']}</strong></p>
        </div>
        
        <div class="config-details">
            <div class="label">📝 Configuration Source:</div>
            <p>This color is loaded from a Kubernetes ConfigMap!</p>
            <p>Mounted at: <code>/config/theme.conf</code></p>
        </div>
        
        <div class="info-box">
            <p><strong>ℹ️ How it works:</strong></p>
            <p>The Kubernetes Deployment mounts a ConfigMap as a file in the pod.</p>
            <p>When the app starts, it reads the configuration from that file.</p>
            <p>To change the color, edit the ConfigMap and restart the pod!</p>
        </div>
    </div>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())

    def handle_config(self):
        """GET /config - Return current configuration as JSON."""
        theme = load_theme_config()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps(theme, indent=2)
        self.wfile.write(response.encode())

    def handle_health(self):
        """GET /health - Health check endpoint."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps({"status": "healthy"})
        self.wfile.write(response.encode())

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_server():
    """Start the HTTP server."""
    port = int(os.getenv('PORT', 5000))
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, ThemeHandler)
    print(f"Dynamic Theme App running on port {port}...")
    print(f"Looking for config at: {CONFIG_FILE}")
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
