#!/usr/bin/env bash
set -euo pipefail

################################################################################
# test-memory-limiter.sh
#
# Purpose:
#   Test the memory limiter app by allocating memory and observing:
#   1. Pod memory usage increases
#   2. Kubernetes throttles or kills the pod when limit is exceeded
#   3. Pod is restarted by the Deployment controller
#
# Usage:
#   ./test-memory-limiter.sh [--increment 50] [--max 250] [--delay 5]
#
# Parameters:
#   --increment  MB to allocate per step (default: 50)
#   --max        Max MB to allocate before stopping (default: 250)
#   --delay      Seconds between allocations (default: 1)
#
# What to observe:
#   - Pod memory usage grows with each allocation
#   - At 256 MB limit, pod may be OOMKilled or throttled
#   - Watch the pod restart count and status changes
#
################################################################################

NAMESPACE="resource-limiter"
LABEL_SELECTOR="app=memory-limiter"
INCREMENT=50          # MB per step
MAX_MB=250            # Stop after this much
DELAY=1               # Seconds between allocations

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --increment) INCREMENT="$2"; shift 2;;
    --max) MAX_MB="$2"; shift 2;;
    --delay) DELAY="$2"; shift 2;;
    -h|--help) 
      echo "Usage: $0 [--increment 50] [--max 250] [--delay 1]"
      exit 0;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

echo "=========================================="
echo "Memory Limiter Test"
echo "=========================================="
echo "Increment: ${INCREMENT} MB per step"
echo "Max allocation: ${MAX_MB} MB"
echo "Delay between steps: ${DELAY} seconds"
echo ""
echo "Watch for:"
echo "  1. Memory usage increasing"
echo "  2. Pod OOMKilled or restarts at 256 MB limit"
echo "  3. Restart count incrementing"
echo ""
echo "Press Ctrl-C to stop."
echo "=========================================="
echo ""

# Get a pod name
POD=$(kubectl get pods -n "$NAMESPACE" -l "$LABEL_SELECTOR" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$POD" ]; then
  echo "ERROR: No pods found for selector '$LABEL_SELECTOR' in namespace '$NAMESPACE'"
  exit 1
fi

echo "Using pod: $POD"
echo ""

# Allocate memory in steps
CURRENT_MB=0

while [ $CURRENT_MB -lt $MAX_MB ]; do
  CURRENT_MB=$((CURRENT_MB + INCREMENT))
  
  echo "====== Step: Allocating ${CURRENT_MB} MB total ======"
  
  # Make the allocation request
  echo "  Sending POST /allocate?mb=${INCREMENT}"
  curl -s -X POST "http://localhost:8080/allocate?mb=${INCREMENT}" | jq '.' || echo "  (Failed or port-forward not available)"
  
  # Check pod memory usage
  echo ""
  echo "  Pod status:"
  kubectl get pod "$POD" -n "$NAMESPACE" -o wide | tail -1 || true
  
  # Check detailed memory from the app
  echo ""
  echo "  Detailed memory info:"
  curl -s "http://localhost:8080/memory" | jq '.memory' || echo "  (Failed or port-forward not available)"
  
  # Check if pod was restarted (OOMKilled)
  RESTART_COUNT=$(kubectl get pod "$POD" -n "$NAMESPACE" -o jsonpath='{.status.containerStatuses[0].restartCount}' 2>/dev/null || echo "0")
  echo ""
  echo "  Pod restart count: $RESTART_COUNT"
  
  # Check for OOMKilled status
  POD_STATUS=$(kubectl get pod "$POD" -n "$NAMESPACE" -o jsonpath='{.status.containerStatuses[0].state}' 2>/dev/null || echo "{}")
  if echo "$POD_STATUS" | grep -q "OOMKilled"; then
    echo ""
    echo "  ⚠️  POD WAS OOMKilled! Waiting for restart..."
    sleep 10
    POD=$(kubectl get pods -n "$NAMESPACE" -l "$LABEL_SELECTOR" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    echo "  Pod restarted as: $POD"
  fi
  
  echo ""
  echo "  Waiting ${DELAY} seconds before next allocation..."
  sleep "$DELAY"
done

echo ""
echo "=========================================="
echo "Test complete. Pod restart count: $RESTART_COUNT"
echo "Check 'kubectl describe pod <pod-name> -n resource-limiter' for details"
echo "=========================================="
