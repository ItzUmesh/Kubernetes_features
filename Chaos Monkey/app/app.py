"""
Simple Flask app that returns a small JSON payload containing the hostname.
Beginners: run this locally to see it work before containerizing.
"""
from flask import Flask, jsonify
import socket

app = Flask(__name__)


@app.route("/")
def index():
    # Return a tiny JSON payload including the container/pod hostname so it's easy
    # to identify which pod served the request when testing in Kubernetes.
    hostname = socket.gethostname()
    return jsonify({"message": "Hello from Chaos Monkey app", "hostname": hostname})


if __name__ == "__main__":
    # For local testing only. In Kubernetes we'll run via Gunicorn defined in Dockerfile.
    app.run(host="0.0.0.0", port=8080, debug=True)
