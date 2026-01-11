# Dynamic Theme App — Kubernetes ConfigMap Example

Learn how Kubernetes ConfigMaps separate configuration from code. This app reads a background color from a mounted ConfigMap and displays it dynamically.

## Overview

The Dynamic Theme App demonstrates a core Kubernetes principle: **configuration should be decoupled from application code**.

Instead of hardcoding colors in the app, we:
- Store the color in a **ConfigMap**
- Mount it as a file in the pod
- The app reads the file at startup
- Change the color by updating the ConfigMap (no code changes!)

## Features

- Simple Python HTTP server (no external dependencies)
- Reads theme configuration from a mounted ConfigMap
- Beautiful HTML page that displays the dynamic background color
- `/health` endpoint for Kubernetes probes
- `/config` endpoint to view the loaded configuration as JSON
- Beginner-friendly: shows exactly how ConfigMaps work

## Project Structure

- `app/` — Python app, Dockerfile, requirements.txt
- `k8s/` — Kubernetes manifests: configmap-deployment.yaml, service.yaml
- `PROCEDURE.md` — Step-by-step walkthrough

## What You'll Learn

1. **ConfigMaps** — How to store configuration in Kubernetes
2. **Volume Mounts** — How pods access external data
3. **Configuration Separation** — Keeping code and config separate
4. **Dynamic Updates** — How to change configuration without redeploying

## Quick Start

1. **Build the Docker image:**
   ```bash
   docker build -t dynamic-theme-app:latest -f ./app/Dockerfile ./app
   ```

2. **Load into kind:**
   ```bash
   kind load docker-image dynamic-theme-app:latest
   ```

3. **Deploy to Kubernetes:**
   ```bash
   kubectl apply -f ./k8s/configmap-deployment.yaml
   kubectl apply -f ./k8s/service.yaml
   ```

4. **Port-forward to the service:**
   ```bash
   kubectl port-forward -n dynamic-theme-demo svc/theme-app-service 8080:80
   ```

5. **Open in browser:**
   ```
   http://localhost:8080
   ```

6. **View the loaded configuration:**
   ```bash
   curl http://localhost:8080/config
   ```

## Key Concepts

### ConfigMap

A Kubernetes object that stores configuration data as key-value pairs. In this project:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: theme-config
data:
  theme.conf: |
    background_color=#3498db
    theme_name=Blue
    title=Dynamic Theme App - Blue Theme
```

### Volume Mount

The Deployment mounts the ConfigMap as a file:

```yaml
volumeMounts:
- name: config
  mountPath: /config
  readOnly: true

volumes:
- name: config
  configMap:
    name: theme-config
    items:
    - key: theme.conf
      path: theme.conf
```

Result: The file is available at `/config/theme.conf` inside the pod.

### Code Reading the Config

```python
def load_theme_config():
    """Load theme configuration from the mounted ConfigMap file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            # Parse key=value pairs
            ...
```

## Endpoints

- `GET /` — Beautiful HTML page with dynamic theme
- `GET /config` — View the loaded configuration as JSON
- `GET /health` — Kubernetes liveness/readiness probe

## See Also

- Full procedure: [PROCEDURE.md](PROCEDURE.md)
- Kubernetes ConfigMaps: https://kubernetes.io/docs/concepts/configuration/configmap/
