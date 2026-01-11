# How the Health Check Works

## Overview

This document explains the internal mechanism of how the Health Check Demo kills and recovers application health status through Kubernetes liveness probes.

---

## The Health State Management

### Global State Variable

The app maintains a simple global boolean flag:

```python
health_state = {"healthy": True}
```

This flag starts as `True` and persists across all HTTP requests until explicitly toggled.

---

## The `/health` Endpoint Behavior

### Healthy State (HTTP 200)

When `health_state["healthy"]` is `True`:

```python
def handle_health(self):
    if health_state["healthy"]:
        self.send_response(200)  # HTTP 200 = Success
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps({"status": "healthy"})
        self.wfile.write(response.encode())
```

**Response:**
```
HTTP/1.0 200 OK
Content-type: application/json

{"status": "healthy"}
```

### Unhealthy State (HTTP 503)

When `health_state["healthy"]` is `False`:

```python
    else:
        self.send_response(503)  # HTTP 503 = Service Unavailable
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps({"status": "unhealthy"})
        self.wfile.write(response.encode())
```

**Response:**
```
HTTP/1.0 503 Service Unavailable
Content-type: application/json

{"status": "unhealthy"}
```

---

## The `/toggle-health` Endpoint (The Kill Switch)

### How It Works

The POST `/toggle-health` endpoint flips the health flag:

```python
def handle_toggle_health(self):
    """POST /toggle-health - Toggle health state."""
    health_state["healthy"] = not health_state["healthy"]
    new_state = "healthy" if health_state["healthy"] else "unhealthy"
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    response = {
        "message": f"Health toggled to {new_state}",
        "current_state": new_state
    }
    self.wfile.write(json.dumps(response).encode())
```

### Example: Killing Health

**Request:**
```bash
curl -X POST http://localhost:8080/toggle-health
```

**Response:**
```json
{
  "message": "Health toggled to unhealthy",
  "current_state": "unhealthy"
}
```

**Result:** `health_state["healthy"]` is now `False`

**Next `/health` check:**
```bash
curl http://localhost:8080/health
```

Returns HTTP 503 (unhealthy).

---

## Kubernetes Liveness Probe Behavior

### Probe Configuration

From `deployment.yaml`:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5      # Wait 5s before first check
  periodSeconds: 5            # Check every 5 seconds
  failureThreshold: 2         # Restart after 2 failures
  timeoutSeconds: 2           # Allow 2s for response
```

### The Restart Sequence

**Timeline of events:**

```
T=0s:    Pod starts, health_state = {"healthy": True}
T=5s:    Liveness probe checks /health → 200 ✓ (pass)
T=10s:   Liveness probe checks /health → 200 ✓ (pass)
T=15s:   User runs: curl -X POST /toggle-health
         health_state["healthy"] = False
T=20s:   Liveness probe checks /health → 503 ✗ (fail #1)
T=25s:   Liveness probe checks /health → 503 ✗ (fail #2)
T=26s:   failureThreshold reached (2 failures)
         Kubernetes kills the pod
T=27s:   Kubernetes starts a new pod (RESTARTS increments)
T=32s:   New pod initializes, health_state defaults to True
T=37s:   Liveness probe checks /health → 200 ✓ (pass)
         Pod is now Running again
```

### Pod State Changes

```bash
kubectl get pods -n health-check-demo -w
```

You'll see:

```
NAME                            READY   STATUS    RESTARTS   AGE
health-check-app-xxxxx-m25xz    1/1     Running   0          2m40s
health-check-app-xxxxx-m25xz    0/1     Running   0          3m5s     # Probe failing
health-check-app-xxxxx-m25xz    1/1     Running   0          3m25s    # Still running, not restarted yet
health-check-app-xxxxx-m25xz    0/1     Running   1 (1s ago)  3m41s    # RESTART! RESTARTS=1
health-check-app-xxxxx-m25xz    1/1     Running   1 (5s ago)  3m45s    # Recovered
```

---

## Full Example: Kill and Recovery Flow

### Step 1: Check Current Health

```bash
curl http://localhost:8080/health
```

Response:
```json
{"status": "healthy"}
```

### Step 2: Toggle to Unhealthy (Kill)

```bash
curl -X POST http://localhost:8080/toggle-health
```

Response:
```json
{
  "message": "Health toggled to unhealthy",
  "current_state": "unhealthy"
}
```

### Step 3: Observe Pod Restart

```bash
kubectl get pods -n health-check-demo -w
```

Watch as `RESTARTS` increments and pod cycles.

### Step 4: Auto-Recovery

After pod restarts, it automatically recovers:

```bash
curl http://localhost:8080/health
```

Response (after restart):
```json
{"status": "healthy"}
```

---

## Why This Works

1. **Stateless Health Management** — The health flag is simple and in-memory; no persistence
2. **HTTP Status Codes** — Kubernetes liveness probes understand HTTP responses (200 = pass, non-200 = fail)
3. **Threshold-Based Restarts** — Multiple failures trigger action (prevents flaky networks)
4. **Clean Restart** — New pod inherits default healthy state

---

## Key Takeaways

- **No manual pod deletion needed** — The app itself controls when it appears unhealthy
- **Kubernetes does the cleanup** — Liveness probe detects failures and restarts automatically
- **Immediate recovery** — Restarted pod defaults to healthy
- **Educational value** — You see the full lifecycle: healthy → inject failure → detect → restart → recover

This pattern is useful for testing application resilience without complex failure injection tools.
