#!/usr/bin/env bash
set -euo pipefail

################################################################################
# chaos-monkey.sh
#
# Purpose:
#   Repeatedly deletes a random pod matching a label selector so you can observe
#   how Kubernetes (Deployment/ReplicaSet) immediately recreates pods to maintain
#   the desired replica count.
#
# High-level flow:
#   1. Parse optional arguments (namespace, label selector, interval).
#   2. In an infinite loop:
#        a) List pods matching the selector.
#        b) Pick one pod at random.
#        c) Delete that pod (optionally forced for fast replacement).
#        d) Sleep for the configured interval and repeat.
#
# Safety flags (explaination):
#   - `set -e`: exit immediately if a command exits with non-zero status (fail-fast).
#   - `set -u`: treat unset variables as errors (helps catch typos).
#   - `set -o pipefail`: cause a pipeline to fail if any component fails.
#
# Note for beginners:
#   - Deleting a pod does NOT delete the Deployment. The Deployment controller
#     will create a replacement pod to keep replicas stable.
#   - This script uses `kubectl` so ensure your kubeconfig/context points to the
#     cluster you want to test.
################################################################################

# Default configuration values; override with flags below.
NAMESPACE=default
LABEL_SELECTOR="app=chaos-monkey"
INTERVAL=10

print_usage() {
  echo "Usage: $0 [--namespace N] [--label \"key=val\"] [--interval S]"
  echo "  --namespace   Kubernetes namespace (default: default)"
  echo "  --label       Pod label selector (default: app=chaos-monkey)"
  echo "  --interval    Seconds between deletions (default: 10)"
}

# Parse command-line arguments (simple loop, no external libraries)
while [[ $# -gt 0 ]]; do
  case "$1" in
    --namespace)
      NAMESPACE="$2"; shift 2;;
    --label)
      LABEL_SELECTOR="$2"; shift 2;;
    --interval)
      INTERVAL="$2"; shift 2;;
    -h|--help)
      print_usage; exit 0;;
    *)
      echo "Unknown arg: $1"; print_usage; exit 1;;
  esac
done

echo "Starting Chaos Monkey: namespace=$NAMESPACE label=$LABEL_SELECTOR interval=${INTERVAL}s"
echo "Press Ctrl-C to stop."

# Handle Ctrl-C (SIGINT) and SIGTERM so the script exits cleanly with a message.
trap 'echo; echo "Stopping Chaos Monkey"; exit 0' SIGINT SIGTERM

# Main loop: run forever until user interrupts
while true; do
  # Get the list of pod names for the selector in the namespace.
  # jsonpath returns each pod name; mapfile reads them into the 'pods' array.
  # Redirect stderr to /dev/null to avoid noisy output if there are no pods or kubectl fails.
  mapfile -t pods < <(kubectl get pods -n "$NAMESPACE" -l "$LABEL_SELECTOR" -o jsonpath='{range .items[*]}{.metadata.name}\n{end}' 2>/dev/null || true)

  # If we didn't find any pods, print a helpful message and retry after the interval.
  if [ ${#pods[@]} -eq 0 ]; then
    echo "No pods found for selector '$LABEL_SELECTOR' in namespace '$NAMESPACE' - retrying in ${INTERVAL}s"
    sleep "$INTERVAL"
    continue
  fi

  # Choose a random pod from the list. `shuf -n 1` returns one random line.
  pod_to_delete=$(printf "%s\n" "${pods[@]}" | shuf -n 1)

  echo "Deleting pod: $pod_to_delete"
  # Delete the pod. The flags used here force immediate deletion:
  #   --grace-period=0 : tells kubelet not to wait for graceful termination
  #   --force          : forces deletion of the API object immediately
  # We add `|| true` so that if the delete command fails for any reason (race condition,
  # transient API error) the script will continue rather than exiting (useful for long runs).
  # Important: forcing deletion may skip graceful shutdown hooks inside your app.
  kubectl delete pod "$pod_to_delete" -n "$NAMESPACE" --grace-period=0 --force || true

  # Wait before deleting another pod. This gives Kubernetes time to schedule a new pod
  # and for you to observe behavior. Adjust `INTERVAL` to speed up or slow down the test.
  sleep "$INTERVAL"
done
