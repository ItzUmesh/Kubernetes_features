# Health Check Demo — Kubernetes Liveness Probe Example

Explore Kubernetes liveness probes by manually toggling an app's health endpoint and watching the pod restart.

## Overview

This project demonstrates how Kubernetes uses liveness probes to keep applications healthy. Deploy a simple Flask app, then toggle its `/health` endpoint to unhealthy and watch Kubernetes automatically restart the pod.

## Features

- Simple Flask app with `/health` endpoint
- Toggleable health state via `/toggle-health` POST endpoint
- Kubernetes Deployment with liveness and readiness probes
- Service for accessing the app
- Manual health toggle to trigger restarts
- Step-by-step procedure in `PROCEDURE.md`

## Project Structure

- `app/` — Flask app, Dockerfile, requirements.txt
- `k8s/` — Kubernetes manifests: deployment.yaml, service.yaml
- `PROCEDURE.md` — full walkthrough and testing steps

## Quick Start

1. **Build the Docker image:**
   ```bash
   docker build -t health-check-app:latest -f ./app/Dockerfile ./app
   ```

2. **Load into kind:**
   ```bash
   kind load docker-image health-check-app:latest
   ```

3. **Deploy to Kubernetes:**
   ```bash
   kubectl apply -f ./k8s/deployment.yaml
   kubectl apply -f ./k8s/service.yaml
   ```

4. **Access the app:**
   ```bash
   kubectl port-forward -n health-check-demo svc/health-check-service 8080:80
   ```

5. **Check health (in another terminal):**
   ```bash
   curl http://localhost:8080/health
   ```

6. **Toggle health to unhealthy:**
   ```bash
   curl -X POST http://localhost:8080/toggle-health
   ```

7. **Watch the pod restart:**
   ```bash
   kubectl get pods -n health-check-demo -w
   ```

## Endpoints

- `GET /` — Basic app info
- `GET /health` — Liveness probe endpoint (returns 200 if healthy, 503 if unhealthy)
- `GET /status` — Detailed health status
- `POST /toggle-health` — Toggle health state (trigger restart)

## How It Works

- **Liveness Probe** — Kubernetes checks `/health` every 5 seconds (initialDelaySeconds: 5)
- **Failure Detection** — If 2 consecutive checks fail (failureThreshold: 2), the pod is restarted
- **Toggle Endpoint** — POST to `/toggle-health` to set health to unhealthy
- **Automatic Recovery** — Pod restarts and health returns to healthy

## See Also

- Full procedure and troubleshooting: [PROCEDURE.md](PROCEDURE.md)
