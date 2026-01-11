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

app = Flask(__name__)

# Global list to hold allocated memory blocks
# Each element is a list of integers, consuming memory
allocated_memory = []

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
    try:
        # 1 MB = 1,048,576 bytes
        # Each int in Python is ~28 bytes
        # So ~37,449 integers per MB
        integers_per_mb = 37449
        total_integers = int(mb * integers_per_mb)
        
        # Create a list of integers (this consumes memory)
        memory_block = list(range(total_integers))
        allocated_memory.append(memory_block)
        
        return True
    except MemoryError:
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
    """
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    # Run Flask app on port 5000
    # Using threaded mode for simplicity
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
