# Config Hot-Reloader — Dynamic Configuration Without Pod Restart

## What You'll Learn

A Python app that watches a ConfigMap-mounted file and **reloads configuration dynamically** without requiring a pod restart. Perfect for demonstrating:

- File watching in Python (using `watchdog`)
- Graceful config reloading with threading
- ConfigMap hot-reload patterns
- Kubernetes file update propagation
- Zero-downtime config updates

## Overview

Traditional Kubernetes approach: edit ConfigMap → pod restart required.

**Better approach (this project)**: edit ConfigMap → file changes detected → app reloads config logic instantly → service never stops.

## Features

- **HTTP endpoints** for status and config queries
- **File watcher** that detects ConfigMap changes in real-time (uses `watchdog`)
- **Thread-safe reloading** with locks to prevent race conditions
- **Reload tracking** — count and timestamp each reload
- **Health checks** for Kubernetes probes
- **Clean logging** to show config changes as they happen

## Quick Start

### Prerequisites

- `kubectl` configured to a running kind cluster
- `docker` installed and running

### 1. Build the Docker image

```bash
cd /path/to/Config-Hot-Reloader
docker build -t config-hot-reloader:latest -f ./app/Dockerfile ./app
```

### 2. Load into kind

```bash
kind load docker-image config-hot-reloader:latest
```

### 3. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f ./k8s/namespace.yaml

# Deploy ConfigMap, Deployment, and Service
kubectl apply -f ./k8s/configmap.yaml
kubectl apply -f ./k8s/deployment.yaml
kubectl apply -f ./k8s/service.yaml
```

Verify pods are running:
```bash
kubectl get pods -n config-hot-reloader
```

### 4. Port-forward to the service

```bash
kubectl port-forward -n config-hot-reloader svc/config-reloader-service 8080:80
```

### 5. View the current config

```bash
curl http://localhost:8080/config | jq .
```

You'll see:
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
  "last_reload": "2026-04-18T...",
  "reload_count": 1
}
```

## The Hot-Reload Demo

### Step 1: Watch logs in real-time

In a separate terminal, watch the app's log output:
```bash
kubectl logs -f -n config-hot-reloader deployment/config-reloader
```

You'll see:
```
[2026-04-18T12:34:56.789] INFO - ✓ Config loaded: { ... }
[2026-04-18T12:34:57.123] INFO - 👀 File watcher started
[2026-04-18T12:34:58.456] INFO - ✓ Server ready...
```

### Step 2: Edit the ConfigMap

In another terminal, edit the ConfigMap:
```bash
kubectl edit configmap app-config -n config-hot-reloader
```

Change the config values, for example:
- Change `"debug_mode": false` to `"debug_mode": true`
- Change `"environment": "production"` to `"environment": "staging"`
- Change the primary color to `"#27ae60"`

Save and exit (`:wq` in vim).

### Step 3: Watch the app reload

**In the logs terminal**, you'll see:
```
[2026-04-18T12:35:15.234] INFO - 📝 Config file changed: /etc/config/app-config.json
[2026-04-18T12:35:15.789] INFO - ✓ Config loaded: { ... }
[2026-04-18T12:35:15.890] INFO - 🔄 Config reloaded (reload #2)
```

**The pod never restarted!** The app detected the file change and reloaded automatically.

### Step 4: Verify the new config is active

```bash
curl http://localhost:8080/config | jq '.current_config.environment'
```

Returns: `"staging"` (the new value!)

Check the reload count:
```bash
curl http://localhost:8080/config | jq '.reload_count'
```

Returns: `2` (or higher if you edited multiple times)

## Endpoints

- **GET /** — App info and endpoint list
- **GET /config** — Current loaded configuration with reload metadata
- **GET /health** — Kubernetes health check
- **GET /status** — Detailed app status including reload info

## How It Works

### The App Architecture

```
┌─────────────────────────────────────┐
│  Python HTTP Server (Port 5000)    │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  RequestHandler             │  │
│  │  (GET /config, /health...)  │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  app_state (thread-safe)    │  │
│  │  - config dict              │  │
│  │  - reload_count             │  │
│  │  - lock (threading.Lock)    │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  watchdog.Observer (thread) │  │
│  │  Monitors /etc/config/      │  │
│  │  Calls reload_config() on   │  │
│  │  file change events         │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
         ↓ (watches)
┌─────────────────────────────────────┐
│  Kubernetes ConfigMap Volume        │
│  /etc/config/app-config.json        │
│  (updated when ConfigMap changes)   │
└─────────────────────────────────────┘
```

### Key Components

1. **HTTP Server** — Handles requests for config, health, status
2. **File Watcher** — Uses `watchdog` library to detect ConfigMap file changes
3. **Reload Logic** — Thread-safe configuration reloading with locks
4. **App State** — Global state dict protected by `threading.Lock()`

### ConfigMap Volume Mounting

In `deployment.yaml`:
```yaml
volumeMounts:
- name: config
  mountPath: /etc/config
  readOnly: false  # Important: must be writable for updates

volumes:
- name: config
  configMap:
    name: app-config
    items:
    - key: app-config.json
      path: app-config.json
```

When the ConfigMap is edited, Kubernetes updates the file at `/etc/config/app-config.json` within seconds. The `watchdog` observer detects this change and triggers a reload.

## Why This Matters

| Approach | Pros | Cons |
|---|---|---|
| **Pod Restart** | Clean slate, simple logic | Downtime, connection drops, slower |
| **Hot-Reload** (this project) | Zero downtime, fast, graceful | More complex, thread-safety needed |

**Use hot-reload for**: Configuration changes that shouldn't interrupt service  
**Use pod restart for**: Major updates that need clean initialization

## Advanced: File Update Propagation Timing

Kubernetes ConfigMap volume updates are **eventually consistent**. Changes may take 1–10 seconds to appear in the pod.

**Key settings in `deployment.yaml`:**
```yaml
volumeMounts:
- name: config
  mountPath: /etc/config
  readOnly: false  # Allow updates to propagate
```

To speed up propagation, you can add:
```yaml
volumes:
- name: config
  configMap:
    name: app-config
    defaultMode: 0644  # Permissions
```

## Troubleshooting

### Config doesn't reload

**Check 1**: Verify the file watcher is running:
```bash
kubectl logs -f -n config-hot-reloader deployment/config-reloader | grep "File watcher"
```

**Check 2**: Manually verify the file changed:
```bash
kubectl exec -it -n config-hot-reloader <pod-name> -- cat /etc/config/app-config.json
```

**Check 3**: Ensure ConfigMap volume is writable (not `readOnly: true`)

### Pod crashes on startup

**Cause**: `watchdog` library not installed or Python version issue

**Solution**:
```bash
# Rebuild image
docker build -t config-hot-reloader:latest -f ./app/Dockerfile ./app
kind load docker-image config-hot-reloader:latest
kubectl rollout restart deployment/config-reloader -n config-hot-reloader
```

### Port-forward connection refused

```bash
kubectl port-forward -n config-hot-reloader svc/config-reloader-service 8080:80
```

Ensure the pod is running:
```bash
kubectl get pods -n config-hot-reloader
```

## Cleanup

```bash
kubectl delete namespace config-hot-reloader
```

## What Clients Will Learn

✅ Configuration can be hot-reloaded without pod restart  
✅ File watching enables dynamic configuration patterns  
✅ Thread-safety is critical for concurrent access  
✅ Kubernetes ConfigMap volumes are eventually consistent  
✅ Zero-downtime configuration updates are possible  
✅ Apps can be resilient and responsive to config changes  

## Next Steps

- **Modify the config schema** — Add new fields and see hot-reload handle them
- **Add config validation** — Reject invalid configs with error messages
- **Implement feature toggles** — Use config flags to toggle features live
- **Add metrics** — Export reload count and timing to Prometheus
- **Combine with operators** — Build a custom resource for config management

---

**For step-by-step procedure with detailed commands, see PROCEDURE.md.**
