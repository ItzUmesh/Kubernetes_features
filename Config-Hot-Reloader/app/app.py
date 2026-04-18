#!/usr/bin/env python3
"""
Config Hot-Reloader Demo

A Flask app that watches a ConfigMap-mounted file and reloads configuration
dynamically without requiring a pod restart. Uses watchdog to detect file changes
and threading to handle reloads gracefully.
"""

import os
import json
import logging
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration file path (mounted from ConfigMap)
CONFIG_FILE = "/etc/config/app-config.json"

# Global config state
app_state = {
    "config": {},
    "last_reload": None,
    "reload_count": 0,
    "lock": threading.Lock(),
}


def load_config():
    """Load configuration from the mounted ConfigMap file."""
    if not os.path.exists(CONFIG_FILE):
        logger.warning(f"Config file not found at {CONFIG_FILE}")
        return {}
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        logger.info(f"✓ Config loaded: {json.dumps(config, indent=2)}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def reload_config():
    """Reload configuration in a thread-safe manner."""
    with app_state["lock"]:
        new_config = load_config()
        app_state["config"] = new_config
        app_state["last_reload"] = datetime.now().isoformat()
        app_state["reload_count"] += 1
        logger.info(f"🔄 Config reloaded (reload #{app_state['reload_count']})")


class ConfigWatcher(FileSystemEventHandler):
    """Watchdog handler to detect ConfigMap file changes."""
    
    def on_modified(self, event):
        if event.src_path.endswith("app-config.json"):
            logger.info(f"📝 Config file changed: {event.src_path}")
            # Add small delay to allow file to be fully written
            time.sleep(0.5)
            reload_config()


def start_file_watcher():
    """Start the watchdog observer to monitor the config directory."""
    observer = Observer()
    event_handler = ConfigWatcher()
    observer.schedule(event_handler, path="/etc/config", recursive=False)
    observer.start()
    logger.info("👀 File watcher started")
    return observer


class RequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Flask-like server."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/":
            return self.handle_root()
        elif self.path == "/config":
            return self.handle_config()
        elif self.path == "/health":
            return self.handle_health()
        elif self.path == "/status":
            return self.handle_status()
        else:
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = json.dumps({"error": "Not Found"})
            self.wfile.write(response.encode())
    
    def handle_root(self):
        """GET / - App info."""
        response = {
            "app": "Config Hot-Reloader Demo",
            "description": "Watch ConfigMap changes and reload without pod restart",
            "endpoints": {
                "GET /": "This info",
                "GET /config": "Current loaded configuration",
                "GET /health": "Health check",
                "GET /status": "App status and reload info"
            }
        }
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def handle_config(self):
        """GET /config - Return current configuration."""
        with app_state["lock"]:
            response = {
                "current_config": app_state["config"],
                "loaded_from": CONFIG_FILE,
                "last_reload": app_state["last_reload"],
                "reload_count": app_state["reload_count"]
            }
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def handle_health(self):
        """GET /health - Health check."""
        response = {"status": "healthy"}
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def handle_status(self):
        """GET /status - Detailed status."""
        with app_state["lock"]:
            response = {
                "app": "Config Hot-Reloader",
                "status": "running",
                "config_present": os.path.exists(CONFIG_FILE),
                "config": app_state["config"],
                "reload_count": app_state["reload_count"],
                "last_reload": app_state["last_reload"],
                "timestamp": datetime.now().isoformat(),
                "server": "Python HTTP Server"
            }
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def log_message(self, format, *args):
        """Suppress default HTTP server logging."""
        logger.info(f"{self.client_address[0]} - {format % args}")


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Config Hot-Reloader Demo")
    logger.info("=" * 60)
    
    # Load initial config
    logger.info("📂 Loading initial configuration...")
    reload_config()
    
    # Start file watcher (runs in background thread)
    logger.info("👀 Starting file watcher...")
    observer = start_file_watcher()
    
    # Start HTTP server
    logger.info("🚀 Starting HTTP server on port 5000...")
    server_address = ("0.0.0.0", 5000)
    httpd = HTTPServer(server_address, RequestHandler)
    
    try:
        logger.info("✓ Server ready. Listening for requests and config changes...")
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n⏹️  Shutting down...")
    finally:
        observer.stop()
        observer.join()
        httpd.server_close()
        logger.info("👋 Goodbye!")


if __name__ == "__main__":
    main()
