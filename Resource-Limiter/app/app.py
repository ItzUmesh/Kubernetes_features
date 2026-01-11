#!/usr/bin/env python3
"""
Memory-intensive Flask application for testing Kubernetes resource limits.

This app allows you to:
1. View current memory usage
2. Allocate memory on-demand via HTTP endpoints
3. Test how Kubernetes handles resource-constrained containers

Endpoints:
  GET  /                   - Show app info and memory usage
  GET  /memory             - Show current memory usage in MB
  POST /allocate?mb=100    - Allocate 100 MB of memory
  POST /deallocate?mb=100  - Deallocate 100 MB of memory
  GET  /health             - Health check endpoint
"""

from flask import Flask, jsonify, request
import os
import psutil
import json
from datetime import datetime
import sys
import threading
import time

app = Flask(__name__)

# Global list to hold allocated memory blocks
# Each element is a list of integers, consuming memory
allocated_memory = []

# Memory limit threshold (in MB) - when to consider the pod unhealthy
# Default 230 MB; override via env var `MEMORY_THRESHOLD_MB`
MEMORY_THRESHOLD_MB = int(os.getenv('MEMORY_THRESHOLD_MB', '230'))

# Counter for allocation failures - if app keeps failing to allocate, it should exit
allocation_failure_count = 0
MAX_ALLOCATION_FAILURES = 5

def _memory_monitor_loop():
    """Background monitor: if RSS exceeds threshold, exit process.
    This guarantees a container restart even if probes are delayed.
    """
    while True:
        try:
            process = psutil.Process(os.getpid())
            rss_mb = process.memory_info().rss / (1024 * 1024)
            if rss_mb > MEMORY_THRESHOLD_MB:
                print(f"[FATAL] Memory monitor: RSS {rss_mb:.2f}MB > threshold {MEMORY_THRESHOLD_MB}MB. Exiting.")
                # Exit the process to trigger container restart
                sys.exit(1)
        except Exception as e:
            print(f"[WARN] Memory monitor error: {e}")
        time.sleep(2)

def start_memory_monitor():
    t = threading.Thread(target=_memory_monitor_loop, daemon=True)
    t.start()

def get_memory_usage():
    """
    Get current memory usage of this process.
    
    Returns:
        dict: Memory info including RSS (resident set size) and percent
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    mem_percent = process.memory_percent()
    
    return {
        'rss_mb': round(mem_info.rss / (1024 * 1024), 2),  # Resident Set Size
        'vms_mb': round(mem_info.vms / (1024 * 1024), 2),  # Virtual Memory Size
        'percent': round(mem_percent, 2),
        'timestamp': datetime.now().isoformat()
    }

def allocate_memory_mb(mb):
    """
    Allocate memory by creating large lists of integers.
    Each integer takes ~28 bytes, so we calculate how many needed.
    
    Args:
        mb: Megabytes to allocate
    
    Returns:
        bool: True if successful, False otherwise
    """
    global allocation_failure_count
    
    try:
        # 1 MB = 1,048,576 bytes
        # Each int in Python is ~28 bytes
        # So ~37,449 integers per MB
        integers_per_mb = 37449
        total_integers = int(mb * integers_per_mb)
        
        # Create a list of integers (this consumes memory)
        memory_block = list(range(total_integers))
        allocated_memory.append(memory_block)
        
        # Reset failure count on success
        allocation_failure_count = 0
        mem = get_memory_usage()
        print(f"[ALLOC] +{mb}MB; RSS={mem['rss_mb']}MB; blocks={len(allocated_memory)}")
        return True
    except MemoryError:
        allocation_failure_count += 1
        print(f"[CRITICAL] MemoryError on allocation attempt #{allocation_failure_count}")
        
        # If we've failed multiple times, the system is under severe memory pressure
        # Trigger a graceful shutdown so Kubernetes can restart us
        if allocation_failure_count >= MAX_ALLOCATION_FAILURES:
            print(f"[FATAL] Hit {MAX_ALLOCATION_FAILURES} allocation failures - exiting to trigger pod restart")
            sys.exit(1)
        
        return False
    except Exception as e:
        print(f"Error allocating memory: {e}")
        return False

def deallocate_memory_mb(mb):
    """
    Deallocate memory by removing allocated blocks.
    
    Args:
        mb: Approximate megabytes to deallocate
    
    Returns:
        bool: True if something was deallocated
    """
    if not allocated_memory:
        return False
    
    # Remove blocks until we've deallocated roughly 'mb'
    try:
        while allocated_memory and mb > 0:
            block = allocated_memory.pop()
            mb -= max(1, len(block) // 37449)  # Rough estimate of MB freed
        return True
    except Exception as e:
        print(f"Error deallocating memory: {e}")
        return False

@app.route('/', methods=['GET'])
def index():
    """
    Show app info and current memory usage.
    """
    mem = get_memory_usage()
    allocated_blocks = len(allocated_memory)
    
    return jsonify({
        'app': 'Memory Resource Limiter',
        'version': '1.0',
        'purpose': 'Test Kubernetes resource limits and container throttling',
        'hostname': os.getenv('HOSTNAME', 'unknown'),
        'memory_usage': mem,
        'allocated_blocks': allocated_blocks,
        'endpoints': {
            'GET /': 'This info',
            'GET /memory': 'Show memory usage',
            'POST /allocate?mb=100': 'Allocate 100 MB',
            'POST /deallocate?mb=100': 'Deallocate 100 MB',
            'GET /health': 'Health check'
        }
    }), 200

@app.route('/memory', methods=['GET'])
def memory():
    """
    Get current memory usage.
    """
    mem = get_memory_usage()
    allocated_blocks = len(allocated_memory)
    
    return jsonify({
        'memory': mem,
        'allocated_blocks': allocated_blocks
    }), 200

@app.route('/allocate', methods=['POST'])
def allocate():
    """
    Allocate memory on-demand.
    
    Query params:
      mb: Megabytes to allocate (default: 10)
    """
    mb = request.args.get('mb', default=10, type=int)
    
    # Safety: don't allow allocating more than 800 MB at once
    if mb > 800:
        return jsonify({
            'status': 'error',
            'message': f'Refusing to allocate {mb} MB (max 800 MB per request)',
            'request_mb': mb
        }), 400
    
    success = allocate_memory_mb(mb)
    
    if success:
        mem = get_memory_usage()
        return jsonify({
            'status': 'success',
            'allocated_mb': mb,
            'memory': mem,
            'allocated_blocks': len(allocated_memory)
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': f'Failed to allocate {mb} MB (system out of memory?)',
            'allocated_mb': mb
        }), 500

@app.route('/deallocate', methods=['POST'])
def deallocate():
    """
    Deallocate memory.
    
    Query params:
      mb: Megabytes to deallocate (default: 10)
    """
    mb = request.args.get('mb', default=10, type=int)
    
    success = deallocate_memory_mb(mb)
    
    if success:
        mem = get_memory_usage()
        return jsonify({
            'status': 'success',
            'deallocated_mb': mb,
            'memory': mem,
            'allocated_blocks': len(allocated_memory)
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': 'No allocated memory to deallocate',
            'allocated_mb': 0
        }), 400

@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint for Kubernetes probes.
    Returns 503 (Service Unavailable) when memory usage is too high.
    This will cause the liveness probe to fail and trigger pod restart.
    """
    mem = get_memory_usage()
    rss_mb = mem['rss_mb']
    
    # If memory usage exceeds threshold, report unhealthy
    if rss_mb > MEMORY_THRESHOLD_MB:
        print(f"[WARNING] Health check FAILED: Memory {rss_mb}MB exceeds threshold {MEMORY_THRESHOLD_MB}MB")
        return jsonify({
            'status': 'unhealthy',
            'reason': f'Memory usage {rss_mb}MB exceeds limit {MEMORY_THRESHOLD_MB}MB',
            'memory': mem
        }), 503
    
    return jsonify({
        'status': 'healthy',
        'memory': mem
    }), 200

if __name__ == '__main__':
    # Run Flask app on port 5000
    # Using threaded mode for simplicity
    # Start background memory monitor
    start_memory_monitor()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
