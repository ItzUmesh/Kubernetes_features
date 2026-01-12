#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import socket
from datetime import datetime

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Environment Switcher</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, {bg_gradient});
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }}
        .env-badge {{
            display: inline-block;
            background: {badge_color};
            color: white;
            padding: 10px 30px;
            border-radius: 25px;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 30px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        h1 {{
            color: #333;
            margin-bottom: 30px;
            font-size: 32px;
        }}
        .info-grid {{
            display: grid;
            gap: 20px;
        }}
        .info-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid {badge_color};
        }}
        .info-label {{
            font-weight: 600;
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        .info-value {{
            color: #333;
            font-size: 18px;
            word-break: break-all;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #999;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div style="text-align: center;">
            <div class="env-badge">{environment}</div>
            <h1>🚀 Environment Switcher</h1>
        </div>
        
        <div class="info-grid">
            <div class="info-card">
                <div class="info-label">Environment</div>
                <div class="info-value">{environment}</div>
            </div>
            
            <div class="info-card">
                <div class="info-label">Hostname</div>
                <div class="info-value">{hostname}</div>
            </div>
            
            <div class="info-card">
                <div class="info-label">Replicas</div>
                <div class="info-value">{replicas}</div>
            </div>
            
            <div class="info-card">
                <div class="info-label">Resource Limits</div>
                <div class="info-value">CPU: {cpu_limit} | Memory: {memory_limit}</div>
            </div>
            
            <div class="info-card">
                <div class="info-label">API Version</div>
                <div class="info-value">{api_version}</div>
            </div>
            
            <div class="info-card">
                <div class="info-label">Debug Mode</div>
                <div class="info-value">{debug_mode}</div>
            </div>
            
            <div class="info-card">
                <div class="info-label">Timestamp</div>
                <div class="info-value">{timestamp}</div>
            </div>
        </div>
        
        <div class="footer">
            Powered by Kustomize | Python HTTP Server
        </div>
    </div>
</body>
</html>
"""

class EnvironmentHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Handle both / and /health paths
        if self.path in ['/', '/health']:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Get environment variables with defaults
            environment = os.getenv('ENVIRONMENT', 'UNKNOWN')
            replicas = os.getenv('REPLICAS', 'N/A')
            cpu_limit = os.getenv('CPU_LIMIT', 'N/A')
            memory_limit = os.getenv('MEMORY_LIMIT', 'N/A')
            api_version = os.getenv('API_VERSION', 'v1.0.0')
            debug_mode = os.getenv('DEBUG_MODE', 'false')
            
            # Set colors based on environment
            if environment.upper() == 'PRODUCTION':
                bg_gradient = '#FF6B6B 0%, #C92A2A 100%'
                badge_color = '#C92A2A'
            elif environment.upper() == 'DEVELOPMENT':
                bg_gradient = '#4ECDC4 0%, #1A535C 100%'
                badge_color = '#1A535C'
            else:
                bg_gradient = '#95A5A6 0%, #7F8C8D 100%'
                badge_color = '#7F8C8D'
            
            # Render HTML with environment data
            html = HTML_TEMPLATE.format(
                environment=environment,
                hostname=socket.gethostname(),
                replicas=replicas,
                cpu_limit=cpu_limit,
                memory_limit=memory_limit,
                api_version=api_version,
                debug_mode=debug_mode,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                bg_gradient=bg_gradient,
                badge_color=badge_color
            )
            
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>404 - Not Found</h1>')
    
    def log_message(self, format, *args):
        # Log requests to stdout
        print(f"{self.address_string()} - [{self.log_date_time_string()}] {format % args}")

def run_server():
    port = int(os.getenv('PORT', 5000))
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, EnvironmentHandler)
    
    print(f"Starting Python HTTP Server on port {port}...")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'UNKNOWN')}")
    print(f"Server running at http://0.0.0.0:{port}/")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    run_server()
