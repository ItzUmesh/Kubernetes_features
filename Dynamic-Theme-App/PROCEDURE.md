# Dynamic Theme App — Step-by-Step Procedure

## Overview

This procedure walks you through deploying the Dynamic Theme App and learning how Kubernetes ConfigMaps work.

---

## Prerequisites

- `kubectl` configured to a running kind cluster
- `docker` installed and running
- Cloned this repository

---

## Step 1: Navigate to the Project

```bash
cd Dynamic-Theme-App
```

---

## Step 2: Build the Docker Image

```bash
docker build -t dynamic-theme-app:latest -f ./app/Dockerfile ./app
```

Verify:
```bash
docker images | grep dynamic-theme-app
```

---

## Step 3: Load into kind

```bash
kind load docker-image dynamic-theme-app:latest
```

---

## Step 4: Deploy to Kubernetes

Deploy both the ConfigMap and the application:

```bash
kubectl apply -f ./k8s/configmap-deployment.yaml
kubectl apply -f ./k8s/service.yaml
```

Verify the deployment:

```bash
kubectl get pods -n dynamic-theme-demo
kubectl get configmap -n dynamic-theme-demo
kubectl get svc -n dynamic-theme-demo
```

Expected output:
```
NAME                        READY   STATUS    RESTARTS   AGE
theme-app-xxxxx-xxxxx       1/1     Running   0          10s
```

---

## Step 5: View the ConfigMap

See the configuration data:

```bash
kubectl get configmap theme-config -n dynamic-theme-demo -o yaml
```

You'll see:
```yaml
data:
  theme.conf: |
    background_color=#3498db
    theme_name=Blue
    title=Dynamic Theme App - Blue Theme
```

---

## Step 6: Port-Forward to the Service

```bash
kubectl port-forward -n dynamic-theme-demo svc/theme-app-service 8080:80
```

Keep this running. The app is now at `http://localhost:8080`.

---

## Step 7: Open the App in Browser (New Terminal)

```bash
curl http://localhost:8080
```

You'll see an HTML page with a **blue background** (the color from the ConfigMap).

---

## Step 8: Check the Loaded Configuration

```bash
curl http://localhost:8080/config
```

Response:
```json
{
  "background_color": "#3498db",
  "title": "Dynamic Theme App - Blue Theme",
  "theme_name": "Blue"
}
```

This confirms the app successfully read the ConfigMap file!

---

## Step 9: Change the Theme (The Fun Part!)

Edit the ConfigMap to change the color:

```bash
kubectl edit configmap theme-config -n dynamic-theme-demo
```

Find the `theme.conf` data and change:

```yaml
# FROM:
background_color=#3498db
theme_name=Blue
title=Dynamic Theme App - Blue Theme

# TO:
background_color=#e74c3c
theme_name=Red
title=Dynamic Theme App - Red Theme
```

Save and exit (`:wq` in vim).

---

## Step 10: Restart the Pod

For the app to read the new configuration, restart the pod:

```bash
kubectl rollout restart deployment/theme-app -n dynamic-theme-demo
```

Watch the pod restart:

```bash
kubectl get pods -n dynamic-theme-demo -w
```

---

## Step 11: Refresh and See the New Color

Refresh your browser or run:

```bash
curl http://localhost:8080
```

**The background is now RED!** (or whatever color you set)

Check the config:

```bash
curl http://localhost:8080/config
```

Returns:
```json
{
  "background_color": "#e74c3c",
  "theme_name": "Red",
  "title": "Dynamic Theme App - Red Theme"
}
```

---

## Key Learning Points

### How ConfigMaps Work

1. **Create** — ConfigMap stores key-value data (like theme.conf)
2. **Mount** — Deployment mounts it as a file in the pod
3. **Read** — App reads the file at startup
4. **Update** — Edit the ConfigMap, restart pod, app reads new data

### The Flow

```
ConfigMap (theme.conf)
        ↓
Mount to /config/theme.conf
        ↓
App reads /config/theme.conf
        ↓
Applies theme to HTML page
        ↓
Browser sees new color
```

### Why This Matters

- **No code changes** — Just edit ConfigMap
- **No rebuilding container** — No docker build needed
- **No redeploying image** — Pod restart picks up new config
- **Clean separation** — Config is separate from code

---

## Try Other Colors

Here are some nice colors to try:

- Green: `#27ae60`
- Purple: `#9b59b6`
- Orange: `#e67e22`
- Teal: `#16a085`
- Pink: `#e91e63`

Edit the ConfigMap and restart to see each one!

---

## Optional: Add New Configuration Fields

Try adding more fields to the ConfigMap:

```yaml
background_color=#3498db
theme_name=Blue
title=My Awesome Theme
text_color=#ffffff
font_size=16
```

Then modify `app.py` to read and use these new fields!

---

## Cleanup

Remove the deployment:

```bash
kubectl delete namespace dynamic-theme-demo
```

---

## What's Next?

- Learn about **Secrets** (like ConfigMaps, but for sensitive data)
- Explore **Environment Variables** as another config method
- Try **Helm** for templating complex configurations
- Build apps that respond to ConfigMap changes without restart (using file watchers)
