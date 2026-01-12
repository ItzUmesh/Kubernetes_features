#!/usr/bin/env python3
"""
Simple Multi-Replica Web Server

This app logs every request with:
- Pod name (which replica)
- Pod IP
- Hostname
- Request details

This helps visualize how traffic is distributed across replicas.
"""

from flask import Flask, jsonify
import os
import socket
from datetime import datetime

app = Flask(__name__)

# Get pod info from environment
POD_NAME = os.getenv('POD_NAME', 'unknown-pod')
POD_IP = os.getenv('POD_IP', 'unknown-ip')
NODE_NAME = os.getenv('NODE_NAME', 'unknown-node')

# Prefer REPLICA_ID from env; otherwise derive from POD_NAME suffix
_env_replica = os.getenv('REPLICA_ID', '').strip()
if _env_replica:
    REPLICA_ID = _env_replica
elif POD_NAME and POD_NAME != 'unknown-pod':
    # Use the last segment after the final dash (common pod naming pattern)
    REPLICA_ID = POD_NAME.rsplit('-', 1)[-1]
else:
    REPLICA_ID = 'unknown'

@app.route('/')
def index():
    """Homepage showing pod info and request details"""
    hostname = socket.gethostname()
    
    log_message = f"[{datetime.now().isoformat()}] Request received by {POD_NAME} (Replica {REPLICA_ID})"
    print(log_message, flush=True)
    
    return jsonify({
        'message': f'Hello from Replica {REPLICA_ID}!',
        'pod_name': POD_NAME,
        'pod_ip': POD_IP,
        'node_name': NODE_NAME,
        'hostname': hostname,
        'replica_id': REPLICA_ID,
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/health')
def health():
    """Health check endpoint for Kubernetes"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/info')
def info():
    """Detailed info about this replica"""
    return jsonify({
        'replica_id': REPLICA_ID,
        'pod_name': POD_NAME,
        'pod_ip': POD_IP,
        'node_name': NODE_NAME,
        'hostname': socket.gethostname(),
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/load')
def load():
    """Simulate some work to observe scheduling"""
    import time
    time.sleep(1)  # Simulate 1 second of work
    return jsonify({
        'message': 'Task completed',
        'replica_id': REPLICA_ID,
        'processing_time_ms': 1000
    }), 200

if __name__ == '__main__':
    print(f"Starting server on {POD_NAME} (Replica {REPLICA_ID})", flush=True)
    app.run(host='0.0.0.0', port=5000, debug=False)
