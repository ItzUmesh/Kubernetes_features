# Health Check Demo — Step-by-Step Procedure

## Overview

This procedure walks you through deploying the Health Check Demo, toggling the health endpoint, and observing Kubernetes liveness probe behavior.

---

## Prerequisites

- `kubectl` configured to a running kind cluster
- `docker` installed and running
- Cloned this repository

---

## Step 1: Navigate to the Project

```bash
cd Health-Check-Demo
```

---

## Step 2: Build the Docker Image

Build the Flask app image:

```bash
docker build -t health-check-app:latest -f ./app/Dockerfile ./app
```

Verify the build:

```bash
docker images | grep health-check-app
```

Expected output:
```
health-check-app   latest   <image-id>   <size>
```

---

## Step 3: Load the Image into kind

```bash
kind load docker-image health-check-app:latest
```

Verify:
```bash
docker exec kind-control-plane ctr images ls | grep health-check
```

---

## Step 4: Deploy to Kubernetes

Create the namespace and deploy the app:

```bash
kubectl apply -f ./k8s/deployment.yaml
kubectl apply -f ./k8s/service.yaml
```

Verify the deployment:

```bash
kubectl get pods -n health-check-demo
kubectl get svc -n health-check-demo
```

Expected pod status: `Running`

---

## Step 5: Port-Forward to the Service

In a terminal, run:

```bash
kubectl port-forward -n health-check-demo svc/health-check-service 8080:80
```

Leave this running. The app is now accessible at `http://localhost:8080`.

---

## Step 6: Check Health Status (Terminal 2)

In another terminal, verify the app is healthy:

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{"status": "healthy"}
```

Check the detailed status:

```bash
curl http://localhost:8080/status
```

Expected response:
```json
{
  "healthy": true,
  "state": "healthy",
  "message": "App is running normally"
}
```

---

## Step 7: Watch Pods (Terminal 3)

Open a third terminal and watch for pod restarts:

```bash
kubectl get pods -n health-check-demo -w
```

This will show changes to the pod status in real-time. Leave this running.

---

## Step 8: Toggle Health to Unhealthy (Terminal 2)

In Terminal 2, toggle the health to unhealthy:

```bash
curl -X POST http://localhost:8080/toggle-health
```

Expected response:
```json
{
  "message": "Health toggled to unhealthy",
  "current_state": "unhealthy"
}
```

---

## Step 9: Observe the Restart

**In Terminal 2**, immediately check health (should fail):

```bash
curl http://localhost:8080/health
```

Expected response (HTTP 503):
```json
{"status": "unhealthy"}
```

**In Terminal 3**, you should see the pod restart within ~10 seconds:
```
NAME                            READY   STATUS    RESTARTS   AGE
health-check-app-xxxxx-aaaaa    1/1     Running   0          5s
health-check-app-xxxxx-aaaaa    0/1     NotReady  0          6s
health-check-app-xxxxx-aaaaa    0/1     Running   1          8s
health-check-app-xxxxx-aaaaa    1/1     Running   1          12s
```

The `RESTARTS` column increments from 0 → 1.

---

## Step 10: Verify Health Recovered

After the pod restarts, it defaults back to healthy. Verify:

```bash
curl http://localhost:8080/health
```

Expected response (HTTP 200):
```json
{"status": "healthy"}
```

The app has automatically recovered!

---

## Understanding the Probes

### Liveness Probe Configuration

From `deployment.yaml`:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 2
  timeoutSeconds: 2
```

- **initialDelaySeconds: 5** — Wait 5 seconds before first check
- **periodSeconds: 5** — Check every 5 seconds
- **failureThreshold: 2** — Restart after 2 consecutive failures
- **timeoutSeconds: 2** — Allow 2 seconds for response

### What Happens

1. Kubernetes calls `GET /health` every 5 seconds
2. If the endpoint returns HTTP 200, the pod is healthy
3. If it returns non-200 (e.g., 503), that's a failure
4. After 2 failures (10 seconds), Kubernetes restarts the pod
5. The restarted pod defaults to healthy state

---

## Troubleshooting

### Pod Never Restarts

- Check the pod logs: `kubectl logs -n health-check-demo <pod-name>`
- Verify the deployment: `kubectl describe pod -n health-check-demo <pod-name>`
- Ensure the liveness probe configuration matches `deployment.yaml`

### Cannot Connect to Service

- Verify the pod is running: `kubectl get pods -n health-check-demo`
- Check the service exists: `kubectl get svc -n health-check-demo`
- Verify port-forward: `kubectl port-forward -n health-check-demo svc/health-check-service 8080:80`

### Health Never Toggles

- Ensure you're hitting the correct endpoint: `/toggle-health` (POST)
- Check the pod logs for errors: `kubectl logs -n health-check-demo -f`

---

## Cleanup

Remove the deployment:

```bash
kubectl delete namespace health-check-demo
```

---

## Next Steps

- Modify `failureThreshold` or `periodSeconds` to see different timing
- Add a `/crash` endpoint that causes the app to exit
- Combine with readiness probes to see traffic rerouting during failures
