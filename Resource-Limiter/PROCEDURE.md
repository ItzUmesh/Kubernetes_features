# PROCEDURE (Manual) — Build, Deploy & Test Resource Limiter

This file describes a step-by-step procedure for deploying and testing the Resource Limiter app.

---

## Prerequisites (manual checks)

Verify your environment before starting:

1. Check Kubernetes context and cluster:
   ```bash
   kubectl config current-context
   kind get clusters
   ```

2. Check system memory (important for this project!):
   ```bash
   free -h
   ```
   You should have at least 4 GB free memory.

3. Verify kind cluster is running:
   ```bash
   kubectl cluster-info
   ```

---

## 1) BUILD — Build the Docker image

### Step A — Navigate to project root
```bash
cd <path-to-Resource-Limiter>
```

### Step B — Build the image
```bash
docker build -t memory-limiter-app:latest -f ./app/Dockerfile ./app
```

Verify the build:
```bash
docker images | grep memory-limiter-app
```

You should see `memory-limiter-app:latest` listed.

---

## 2) LOAD — Load image into kind cluster

### Step A — Get your kind cluster name
```bash
kind get clusters
```

### Step B — Load the image
```bash
kind load docker-image memory-limiter-app:latest --name <cluster-name>
```

Example:
```bash
kind load docker-image memory-limiter-app:latest --name kind
```

---

## 3) DEPLOY — Deploy to Kubernetes

### Step A — Apply deployment manifest
```bash
kubectl apply -f ./k8s/deployment.yaml
```

This creates:
- Namespace: `resource-limiter`
- Deployment: `memory-limiter-deployment` with 2 replicas

### Step B — Apply service manifest
```bash
kubectl apply -f ./k8s/service.yaml
```

### Step C — Apply resource quota
```bash
kubectl apply -f ./k8s/resource-quota.yaml
```

This enforces namespace-level resource limits.

### Step D — Verify deployment
```bash
kubectl get pods -n resource-limiter
kubectl get deployment -n resource-limiter
kubectl get resourcequota -n resource-limiter
```

All pods should show `READY 1/1` and `STATUS Running` within 10-15 seconds.

---

## 4) TEST — Test resource limits

### Step A — Port-forward to the service
In one terminal:
```bash
kubectl port-forward -n resource-limiter svc/memory-limiter-service 8080:80
```

Keep this terminal open.

### Step B — View app information
In another terminal:
```bash
curl http://localhost:8080/ | jq '.'
```

Response will show:
- App info
- Current memory usage
- Available endpoints

### Step C — Check current memory
```bash
curl http://localhost:8080/memory | jq '.'
```

Note the `rss_mb` (actual memory used).

---

## 5) OBSERVE — Watch Kubernetes handle resource limits

### Step A — In a new terminal, watch pods in real-time
```bash
kubectl get pods -n resource-limiter -w
```

Leave this running so you can see status changes.

### Step B — Allocate memory in steps

**First allocation (50 MB):**
```bash
curl -X POST http://localhost:8080/allocate?mb=50 | jq '.'
```

Check the response:
- `status`: "success" if allocated
- `memory.rss_mb`: should increase

**Continue allocating in steps:**
```bash
# Allocate another 50 MB
curl -X POST http://localhost:8080/allocate?mb=50 | jq '.'
sleep 3

# Allocate another 50 MB
curl -X POST http://localhost:8080/allocate?mb=50 | jq '.'
sleep 3

# Allocate another 50 MB
curl -X POST http://localhost:8080/allocate?mb=50 | jq '.'
```

### Step C — Observe what happens at the memory limit

The pod has a 256 MB memory limit. Keep allocating until you reach ~200 MB.

**Expected behavior:**

1. **Memory increases with each allocation:**
   ```bash
   curl http://localhost:8080/memory | jq '.memory.rss_mb'
   ```

2. **Pod status remains Running** while memory < 256 MB

3. **At ~256 MB limit:**
   - Pod status changes to `Terminating`
   - Pod is killed due to OOMKilled (Out-Of-Memory)
   - Deployment restarts the pod automatically
   - Watch the pod name change in the `-w` terminal
   - Restart count increments

4. **New pod starts fresh:**
   - Memory usage resets to ~60-80 MB (baseline)
   - You can allocate again

### Step D — View pod details

Check why a pod was killed:
```bash
kubectl describe pod <pod-name> -n resource-limiter
```

Look for in the **Events** section:
```
Killing container due to memory limit
OOMKilled: true
```

Or in **Container Status**:
```
Last State:
  Terminated
    Reason: OOMKilled
    Exit Code: 137
```

---

## 6) ADVANCED — Automated test script

Run the test script to automate memory allocations:

```bash
chmod +x ./scripts/test-memory-limiter.sh
./scripts/test-memory-limiter.sh --increment 50 --max 250 --delay 5
```

This script:
- Allocates 50 MB at a time
- Waits 5 seconds between allocations
- Stops at 250 MB total
- Shows pod status and memory info at each step
- Detects OOMKilled events

---

## 7) RESOURCE QUOTA TESTING

### Step A — Check namespace quota usage

```bash
kubectl describe resourcequota -n resource-limiter
```

You'll see:
```
Name:       resource-limiter-quota
Namespace:  resource-limiter
...
Resource          Used    Hard
--------          ----    ----
limits.cpu        1000m   1000m
limits.memory     512Mi   1Gi
pods              2       10
requests.cpu      200m    500m
requests.memory   128Mi   512Mi
```

### Step B — Try to exceed quota limits

Try to scale up to 5 replicas:
```bash
kubectl scale deployment memory-limiter-deployment -n resource-limiter --replicas 5
```

**Expected result:**

Pods will fail to schedule because the deployment tries to use more memory than the quota allows:

```
Error from server (Forbidden): error when patching ...
"exceeds 'limits.memory'"
```

Check failed pods:
```bash
kubectl get pods -n resource-limiter
```

You'll see pods stuck in `Pending` state.

### Step C — View the quota details

```bash
kubectl describe resourcequota resource-limiter-quota -n resource-limiter
```

Look for the `Status` section showing why pods can't be created.

---

## 8) STOP — Clean up resources

### Step A — Stop port-forward
Press `Ctrl-C` in the port-forward terminal.

### Step B — Delete the namespace and all resources
```bash
kubectl delete namespace resource-limiter
```

This removes:
- All pods
- The deployment
- The service
- The resource quota
- The entire namespace

Verify deletion:
```bash
kubectl get pods -n resource-limiter
```

You should get:
```
error: the server doesn't have a resource type "pod" in API group "v1"
or
No resources found in resource-limiter namespace.
```

---

## Troubleshooting

### Pod stuck in `Pending` state

**Cause:** Node doesn't have enough memory for the pod's `requests`.

**Check:**
```bash
kubectl describe pod <pod-name> -n resource-limiter
```

Look for:
```
Events:
  ...insufficient memory...
```

**Solution:**
- Reduce pod replicas: `kubectl scale deployment memory-limiter-deployment -n resource-limiter --replicas 1`
- Check system memory: `free -h`

### Port-forward fails

**Cause:** Service or pod not running.

**Check:**
```bash
kubectl get svc -n resource-limiter
kubectl get pods -n resource-limiter
```

**Solution:**
- Ensure pods are `Running`: `kubectl get pods -n resource-limiter`
- Restart port-forward: `kubectl port-forward -n resource-limiter svc/memory-limiter-service 8080:80`

### Allocation fails or app returns errors

**Cause:** Pod already OOMKilled or container crashed.

**Check pod logs:**
```bash
kubectl logs <pod-name> -n resource-limiter
```

**Solution:**
- Delete the deployment and redeploy: `kubectl delete deployment memory-limiter-deployment -n resource-limiter`
- Reapply: `kubectl apply -f ./k8s/deployment.yaml`

### System becomes unresponsive

**Warning:** If you allocate too much memory at once, your VM may become sluggish.

**Immediate actions:**
1. Stop allocating (close the curl loop)
2. Delete the deployment: `kubectl delete deployment -n resource-limiter memory-limiter-deployment`
3. Wait for pods to terminate (30 seconds)
4. Check memory: `free -h`

If still slow, restart Docker or the kind cluster.

---

## Summary

This procedure demonstrates:

1. **Building** a memory-intensive Flask app
2. **Loading** the image into kind
3. **Deploying** with resource limits and requests
4. **Testing** by allocating memory until limits are hit
5. **Observing** Kubernetes throttle/kill the container
6. **Enforcing** namespace-level quotas
7. **Troubleshooting** resource-constrained workloads

---

**For more details, see [README.md](README.md).**
