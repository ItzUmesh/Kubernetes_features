# Resource Limiter — Kubernetes Resource Limits & Quotas Demo

## What This Project Teaches

1. **Resource Requests** — Minimum needed to schedule
2. **Resource Limits** — Maximum allowed before throttling/kill
3. **Throttling** — CPU capping under load
4. **OOMKilled** — Behavior when memory limits are exceeded
5. **Resource Quotas** — Namespace-wide guardrails

## Project Structure

```
Resource-Limiter/
├── app/
│   ├── app.py              # Flask app with memory allocation endpoints
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Container image definition
├── k8s/
│   ├── deployment.yaml     # Deployment with resource limits/requests
│   ├── service.yaml        # Service for accessing the app
│   └── resource-quota.yaml # Namespace-level resource quota
├── scripts/
│   └── test-memory-limiter.sh  # Script to test memory allocation
└── README.md               # This file
```

## The Memory Limiter App

A Flask app that lets you:

- **View current memory usage** — GET `/` or `/memory`
- **Allocate memory on-demand** — POST `/allocate?mb=100`
- **Deallocate memory** — POST `/deallocate?mb=100`
- **Health check** — GET `/health`

### Key Features

- Tracks allocated memory in real-time
- Provides memory usage stats (RSS, VMS, percentage)
- Safely limits allocations (max 800 MB per request)
- Returns JSON responses for easy parsing
- Health returns 503 when memory exceeds an app-configured threshold
- Background monitor exits the process to trigger a clean pod restart

### Configuration

- `MEMORY_THRESHOLD_MB` (env): default `230`. When RSS exceeds this, `/health` returns 503 and a background monitor exits the process so Kubernetes restarts the pod.

## Resource Limits Explained

In `deployment.yaml`, each pod has:

```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "500m"
```

- **Requests** — Kubernetes reserves this much on the node. Pod won't schedule if node doesn't have it.
- **Limits** — Pod will be throttled (CPU) or killed (Memory) if it exceeds this.

### What Happens When Limits Are Exceeded

**CPU Limit (500m = 0.5 core):**
- Pod is throttled — CPU time is limited, but the process continues running.

**App Threshold (~230 MB by default):**
- `/health` returns 503 when RSS crosses the threshold
- A background monitor exits the process; Kubernetes restarts the container
- `restartCount` increments in `kubectl get pods`

**Kubernetes Memory Limit (256 MB):**
- If RSS grows beyond the pod limit, Kubernetes may **OOMKill** the container
- You’ll see `Reason: OOMKilled` in `describe pod` and restart behavior

## Quick Start

### Prerequisites

- `kubectl` configured to a running kind cluster
- `docker` installed and running

### 1. Build the Docker Image

```bash
cd <path-to-Resource-Limiter>
docker build -t memory-limiter-app:latest -f ./app/Dockerfile ./app
```

Verify:
```bash
docker images | grep memory-limiter-app
```

### 2. Load Image into kind

```bash
kind load docker-image memory-limiter-app:latest --name kind
```

### 3. Create Namespace and Deploy

```bash
kubectl apply -f ./k8s/deployment.yaml
kubectl apply -f ./k8s/service.yaml
kubectl apply -f ./k8s/resource-quota.yaml
```

Verify deployment:
```bash
kubectl get pods -n resource-limiter
kubectl get deployment -n resource-limiter
```

### 4. Test the App

**Port-forward to the service:**
```bash
kubectl port-forward -n resource-limiter svc/memory-limiter-service 8080:80
```

**In another terminal, test endpoints:**
```bash
# View app info and memory usage
curl http://localhost:8080/

# Allocate 50 MB
curl -X POST http://localhost:8080/allocate?mb=50

# Allocate another 50 MB
curl -X POST http://localhost:8080/allocate?mb=50

# Check memory usage
curl http://localhost:8080/memory

# Health
curl http://localhost:8080/health
```

### 5. Trigger Health Failure and Observe Restarts

Keep running allocations until you cross the app threshold (~230 MB) or the Kubernetes limit (256 MB):

```bash
for i in {1..6}; do 
  echo "=== Allocation $i ==="
  curl -X POST http://localhost:8080/allocate?mb=50 | jq .
  sleep 3
  kubectl get pods -n resource-limiter
  sleep 2
done
```

**What to observe:**
- Pod memory usage increases with each allocation
- At ~230 MB, `/health` returns 503; the process exits and the pod restarts
- If you exceed 256 MB, Kubernetes may OOMKill the container
- Restart count increments in `kubectl get pods`

Tip: to stress a single replica instead of load-balancing via the Service, port-forward directly to one pod:
```bash
POD=$(kubectl get pod -n resource-limiter -l app=memory-limiter -o jsonpath='{.items[0].metadata.name}')
kubectl port-forward -n resource-limiter pod/$POD 9090:5000

# Then use http://localhost:9090 for requests
```

### 6. View Pod Details

```bash
kubectl describe pod <pod-name> -n resource-limiter
```

Look for:
- **Restart Count** — increases when pod is killed
- **Last State** — shows "OOMKilled: true" if memory limit was exceeded
- **Events** — shows "Killing container due to memory limit"

## Advanced: Using the Test Script

```bash
chmod +x ./scripts/test-memory-limiter.sh
./scripts/test-memory-limiter.sh --increment 50 --max 250 --delay 5
```

This automates memory allocation in steps, observing pod behavior.

It can also be used with a direct pod port-forward (`9090:5000`) to observe `restartCount` on a specific pod.

## Resource Quota

`resource-quota.yaml` enforces limits on the entire namespace:

```yaml
hard:
  requests.memory: "512Mi"
  limits.memory: "1Gi"
  pods: "10"
```

This means:
- Total memory **requested** by all pods cannot exceed 512 MB
- Total memory **limit** for all pods cannot exceed 1 GB
- Maximum 10 pods in the namespace

**Test quota limits:**
```bash
# Try to create more pods than the quota allows
kubectl scale deployment memory-limiter-deployment -n resource-limiter --replicas 5
```

You'll see:
```
Error from server (Forbidden): error when patching "memory-limiter-deployment.apps/memory-limiter-deployment": ...
"exceeds 'limits.memory'", "exceeds 'requests.memory'"
```

## Common Issues & Troubleshooting

### Pod stuck in `Pending` state

**Cause:** Node doesn't have enough memory for the `requests`.

**Solution:**
```bash
kubectl describe pod <pod-name> -n resource-limiter
```

Look for "Insufficient memory" warning. Increase available resources or reduce pod count.

### Port-forward fails

**Solution:**
```bash
kubectl port-forward -n resource-limiter svc/memory-limiter-service 8080:80
```

Ensure service exists:
```bash
kubectl get svc -n resource-limiter
```

If a local port (e.g., 8080 or 9090) is already in use, pick a different one: `9191:80`.

### Pod won't allocate memory (allocation fails)

**Cause:** Already at memory limit.

**Solution:**
```bash
# Deallocate memory
curl -X POST http://localhost:8080/deallocate?mb=50

# Check memory usage
curl http://localhost:8080/memory

# Health (503 when threshold exceeded)
curl http://localhost:8080/health
```

### System running out of memory

**Warning:** This demo can consume significant system memory if you allocate too much across all pods.

**Monitor system memory:**
```bash
free -h
```

**If VM becomes sluggish:**
1. Stop allocating immediately
2. Delete the deployment: `kubectl delete deployment -n resource-limiter memory-limiter-deployment`
3. Check remaining memory: `free -h`

## Learning Outcomes

After completing this project, you'll understand:

✅ How to set resource requests and limits in Kubernetes  
✅ How Kubernetes schedules pods based on requests  
✅ How Kubernetes throttles CPU-heavy containers  
✅ How Kubernetes kills memory-heavy containers (OOMKilled)  
✅ How to use resource quotas to enforce namespace-level limits  
✅ How to monitor and debug resource-constrained pods  
✅ Best practices for right-sizing container resources  

## Cleanup

```bash
# Delete the deployment and service
kubectl delete namespace resource-limiter

# Or delete individual resources
kubectl delete -f ./k8s/
```

This will also delete the namespace and all pods within it.

---

**For step-by-step procedures, see PROCEDURE.md.**
