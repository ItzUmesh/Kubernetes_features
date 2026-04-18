# Config Hot-Reloader — Step-by-Step Procedure

## Overview

This procedure walks you through deploying the Config Hot-Reloader app and demonstrating dynamic config reloading without pod restart.

---

## Prerequisites

- `kubectl` configured to a running kind cluster
- `docker` installed and running
- Cloned this repository

---

## Step 1: Navigate to the Project

```bash
cd /path/to/Config-Hot-Reloader
```

Verify the structure:
```bash
ls -la  # Should show: app/, k8s/, README.md, PROCEDURE.md
```

---

## Step 2: Build the Docker Image

```bash
docker build -t config-hot-reloader:latest -f ./app/Dockerfile ./app
```

Verify the build:
```bash
docker images | grep config-hot-reloader
```

Expected output:
```
config-hot-reloader      latest      <image-id>   <size>
```

---

## Step 3: Load the Image into kind

```bash
kind load docker-image config-hot-reloader:latest
```

Verify:
```bash
docker exec kind-control-plane ctr -n k8s.io images ls | grep config-hot-reloader
```

If this still returns nothing, reload the image and check again:
```bash
kind load docker-image config-hot-reloader:latest
docker exec kind-control-plane ctr -n k8s.io images ls | grep config-hot-reloader
```

---

## Step 4: Create Namespace

```bash
kubectl apply -f ./k8s/namespace.yaml
```

Verify:
```bash
kubectl get namespaces | grep config-hot-reloader
```

---

## Step 5: Deploy ConfigMap

```bash
kubectl apply -f ./k8s/configmap.yaml
```

Verify the ConfigMap was created:
```bash
kubectl get configmap -n config-hot-reloader
```

View the config data:
```bash
kubectl get configmap app-config -n config-hot-reloader -o yaml
```

You should see the JSON configuration.

---

## Step 6: Deploy the Application

Deploy the Deployment:
```bash
kubectl apply -f ./k8s/deployment.yaml
```

Deploy the Service:
```bash
kubectl apply -f ./k8s/service.yaml
```

Verify pods are running:
```bash
kubectl get pods -n config-hot-reloader
```

Expected output:
```
NAME                                READY   STATUS    RESTARTS   AGE
config-reloader-xxxxxx-yyyyy       1/1     Running   0          10s
```

---

## Step 7: Port-Forward to the Service

In a **dedicated terminal**, run:

```bash
kubectl port-forward -n config-hot-reloader svc/config-reloader-service 8080:80
```

Leave this running. You should see:
```
Forwarding from 127.0.0.1:8080 -> 5000
```

---

## Step 8: View Initial Configuration (Terminal 2)

In another terminal, view the current config:

```bash
curl http://localhost:8080/ | jq .
```

Expected response:
```json
{
  "app": "Config Hot-Reloader Demo",
  "description": "Watch ConfigMap changes and reload without pod restart",
  "endpoints": { ... }
}
```

View the loaded configuration:
```bash
curl http://localhost:8080/config | jq .
```

Expected response:
```json
{
  "current_config": {
    "app_name": "Config Hot-Reloader Demo",
    "environment": "production",
    "debug_mode": false,
    "log_level": "INFO",
    "feature_flags": { ... },
    "theme": { ... }
  },
  "loaded_from": "/etc/config/app-config.json",
  "last_reload": "2026-04-18T12:34:56.789123",
  "reload_count": 1
}
```

Note the `reload_count: 1` — this is the initial load.

---

## Step 9: Watch Application Logs (Terminal 3)

In a third terminal, watch the logs in real-time:

```bash
kubectl logs -f -n config-hot-reloader deployment/config-reloader
```

You should see:
```
[2026-04-18T12:34:56.789] INFO - ===============================================
[2026-04-18T12:34:56.789] INFO - Config Hot-Reloader Demo
[2026-04-18T12:34:56.789] INFO - ===============================================
[2026-04-18T12:34:57.123] INFO - 📂 Loading initial configuration...
[2026-04-18T12:34:57.234] INFO - ✓ Config loaded: { ... }
[2026-04-18T12:34:57.890] INFO - 👀 File watcher started
[2026-04-18T12:34:58.456] INFO - 🚀 Starting HTTP server on port 5000...
[2026-04-18T12:34:58.567] INFO - ✓ Server ready. Listening for requests and config changes...
```

**Keep this terminal open to watch for config changes.**

---

## Step 10: Edit the ConfigMap (Terminal 2)

In Terminal 2, open the ConfigMap editor:

```bash
kubectl edit configmap app-config -n config-hot-reloader
```

This will open in `vi` or your default editor. Find the `app-config.json` data section and make these changes:

**Original:**
```json
{
  "app_name": "Config Hot-Reloader Demo",
  "environment": "production",
  "debug_mode": false,
  "log_level": "INFO",
  "feature_flags": {
    "cache_enabled": true,
    "analytics": true,
    "beta_features": false
  },
  "theme": {
    "primary_color": "#3498db",
    "accent_color": "#e74c3c"
  }
}
```

**Modified (change these values):**
```json
{
  "app_name": "Config Hot-Reloader Demo - UPDATED",
  "environment": "staging",
  "debug_mode": true,
  "log_level": "DEBUG",
  "feature_flags": {
    "cache_enabled": false,
    "analytics": false,
    "beta_features": true
  },
  "theme": {
    "primary_color": "#27ae60",
    "accent_color": "#f39c12"
  }
}
```

Save and exit (`:wq` in vi).

---

## Step 11: Observe the Hot-Reload (Terminal 3)

**In the logs terminal**, you should see:

```
[2026-04-18T12:35:15.234] INFO - 📝 Config file changed: /etc/config/app-config.json
[2026-04-18T12:35:15.789] INFO - ✓ Config loaded: { "app_name": "Config Hot-Reloader Demo - UPDATED", ... }
[2026-04-18T12:35:15.890] INFO - 🔄 Config reloaded (reload #2)
```

**Key observation**: The pod never restarted! The file change was detected and the config reloaded automatically.

---

## Step 12: Verify New Config is Active (Terminal 2)

Check the config again:

```bash
curl http://localhost:8080/config | jq '.current_config.environment'
```

Returns: `"staging"` (the new value!)

Check another field:
```bash
curl http://localhost:8080/config | jq '.current_config.debug_mode'
```

Returns: `true` (updated!)

Check the reload count:
```bash
curl http://localhost:8080/config | jq '.reload_count'
```

Returns: `2` (reloaded once from the initial load)

Check the timestamp:
```bash
curl http://localhost:8080/config | jq '.last_reload'
```

Should be **recent** (when you edited the ConfigMap).

---

## Step 13: Verify Pod Stability

Check the pod status to confirm **no restart occurred**:

```bash
kubectl get pods -n config-hot-reloader
```

Look for the `RESTARTS` column — it should be `0`:
```
NAME                                READY   STATUS    RESTARTS   AGE
config-reloader-xxxxxx-yyyyy       1/1     Running   0          5m
```

If RESTARTS were > 0, the pod would have restarted. But it didn't — the reload was hot!

---

## Step 14: Repeat the Hot-Reload Cycle

Edit the ConfigMap again:
```bash
kubectl edit configmap app-config -n config-hot-reloader
```

Change more values (e.g., flip `beta_features` to `false`, change a color).

Watch the logs reload again, then verify with:
```bash
curl http://localhost:8080/config | jq '.reload_count'
```

It should increment (e.g., `3`, `4`, etc.).

---

## Step 15: Advanced — Check File Propagation Timing

Kubernetes ConfigMap volume updates take **1–10 seconds** to propagate to pods. You can observe this timing:

1. Edit the ConfigMap and note the time
2. Watch the logs for the "Config file changed" message
3. Calculate the delay

```bash
# Note your start time (Terminal 2)
kubectl edit configmap app-config -n config-hot-reloader
# ...edit and save...

# In Terminal 3, note the time when you see:
# [HH:MM:SS] INFO - 📝 Config file changed...

# Typical delay: 1-5 seconds
```

This demonstrates **eventual consistency** — Kubernetes guarantees the file will be updated, but not instantly.

---

## Step 16: Check App Status

Get detailed status:
```bash
curl http://localhost:8080/status | jq .
```

Full response shows:
- Current loaded config
- Reload count and timestamp
- Whether config file exists
- Pod health

---

## Step 17: Stop the Project (Pause or Fully Remove)

Use this when you are done testing and want to stop all running activity.

### Option A — Quick Stop (Keep Resources, Stop App)

This keeps namespace, ConfigMap, Service, and Deployment objects, but stops running pods.

1. Stop foreground terminals:
  - In the port-forward terminal, press `Ctrl-C`
  - In the logs terminal, press `Ctrl-C`

2. Scale app to zero replicas:
```bash
kubectl scale deployment config-reloader -n config-hot-reloader --replicas=0
```

3. Verify app is stopped:
```bash
kubectl get pods -n config-hot-reloader
kubectl get deployment config-reloader -n config-hot-reloader
```

Expected:
- No running pods
- Deployment shows `0/0` ready replicas

To restart later:
```bash
kubectl scale deployment config-reloader -n config-hot-reloader --replicas=1
kubectl get pods -n config-hot-reloader -w
```

### Option B — Full Stop (Complete Cleanup)

This removes everything created by this project.

1. Stop foreground terminals:
  - In the port-forward terminal, press `Ctrl-C`
  - In the logs terminal, press `Ctrl-C`

2. Delete the namespace:
```bash
kubectl delete namespace config-hot-reloader
```

3. Verify resources are gone:
```bash
kubectl get ns config-hot-reloader
kubectl get all -n config-hot-reloader
```

Expected:
- Namespace not found
- No resources remaining for this project

---

## Cleanup

### Stop port-forward

In Terminal 1, press `Ctrl-C` to stop the port-forward.

### Delete the namespace

```bash
kubectl delete namespace config-hot-reloader
```

Verify deletion:
```bash
kubectl get pods -n config-hot-reloader
```

Should return:
```
error: the server doesn't have a resource type "pod" in API group "v1" in the namespace "config-hot-reloader"
```

---

## Key Learnings

### ✅ What You Demonstrated

1. **Zero-downtime configuration updates** — Config changed without pod restart
2. **File watching in Kubernetes** — File changes detected within seconds
3. **Thread-safe state management** — Concurrent requests handled safely during reload
4. **ConfigMap volume propagation** — File updated when ConfigMap changed
5. **Eventual consistency** — Kubernetes guarantees updates within reasonable time

### ✅ Concepts Covered

- ConfigMap volume mounts
- File watching with `watchdog`
- Thread safety with `threading.Lock()`
- Graceful config reloading
- Kubernetes file update propagation
- HTTP endpoints for observability

### ✅ Why This Matters

**Traditional approach:**
```
Edit ConfigMap → Pod restart → Service interruption → Traffic drop
```

**This project:**
```
Edit ConfigMap → File updated → App detects change → Config reloaded → Service continues
```

---

## Troubleshooting

### Config doesn't reload

**Check 1**: Verify file watcher is running
```bash
kubectl logs -n config-hot-reloader deployment/config-reloader | grep "File watcher started"
```

**Check 2**: Verify the file was actually updated
```bash
kubectl exec -it -n config-hot-reloader <pod-name> -- cat /etc/config/app-config.json
```

**Check 3**: Verify the volume is not read-only
In `deployment.yaml`, ensure:
```yaml
volumeMounts:
- name: config
  mountPath: /etc/config
  readOnly: false  # MUST be false
```

### Logs show errors reading config

**Cause**: ConfigMap file not yet propagated or invalid JSON

**Solution**: Wait 5-10 seconds and check if file appears:
```bash
kubectl exec -it -n config-hot-reloader <pod-name> -- ls -la /etc/config/
```

### Port-forward fails

**Solution**: Verify pod is running and service exists:
```bash
kubectl get pods -n config-hot-reloader
kubectl get svc -n config-hot-reloader
```

Then restart port-forward:
```bash
kubectl port-forward -n config-hot-reloader svc/config-reloader-service 8080:80
```

---

## Summary

This procedure demonstrated:

1. Building and deploying a config hot-reloader app
2. Watching file changes trigger automatic config reloading
3. Zero-downtime configuration updates
4. Thread-safe state management
5. Kubernetes ConfigMap volume behavior

**Key insight**: Modern applications can detect and react to configuration changes without requiring pod restarts, enabling truly elastic and responsive infrastructure.

---

**For more details, see [README.md](README.md).**
