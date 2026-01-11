#!/usr/bin/env python3
"""
Health Check Demo App

A simple Flask app with a /health endpoint that can be toggled to fail,
triggering Kubernetes liveness probe restarts.
"""

import os
import json
from flask import Flask, jsonify, request

app = Flask(__name__)

# Global health state (defaults to healthy)
health_state = {"healthy": True}


@app.route('/', methods=['GET'])
def index():
    """Return basic app info."""
    return jsonify({
        "app": "Health-Check-Demo",
        "version": "1.0",
        "status": "running",
        "hostname": os.getenv('HOSTNAME', 'unknown')
    })


@app.route('/health', methods=['GET'])
def health():
    """
    Liveness probe endpoint.
    Returns 200 if healthy, 503 if unhealthy.
    """
    if health_state["healthy"]:
        return jsonify({"status": "healthy"}), 200
    else:
        return jsonify({"status": "unhealthy"}), 503


@app.route('/toggle-health', methods=['POST'])
def toggle_health():
    """
    Toggle the health state.
    Useful for testing liveness probe behavior.
    """
    health_state["healthy"] = not health_state["healthy"]
    new_state = "healthy" if health_state["healthy"] else "unhealthy"
    return jsonify({
        "message": f"Health toggled to {new_state}",
        "current_state": new_state
    }), 200


@app.route('/status', methods=['GET'])
def status():
    """Return current health state details."""
    return jsonify({
        "healthy": health_state["healthy"],
        "state": "healthy" if health_state["healthy"] else "unhealthy",
        "message": "App is running normally" if health_state["healthy"] else "App is in unhealthy state"
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
