# Kubernetes Practise Demos — Client Presentation Guide

Welcome to our **hands-on Kubernetes demonstration suite**. This collection showcases core Kubernetes concepts through interactive, real-world examples you can run immediately on your local cluster.

---

## 📋 Prerequisites

Before running any demo, ensure you have:

- **Kubernetes cluster**: kind (Kubernetes in Docker) or minikube running locally
- **Docker**: Installed and running (`docker --version`)
- **kubectl**: Installed and configured (`kubectl cluster-info`)
- **System resources**: 4+ GB free RAM recommended

**Quick setup (if needed):**
```bash
kind create cluster
kubectl cluster-info
```

---

## 🎯 The Six Core Demos

### 1️⃣ Dynamic-Theme-App — Configuration Management ⏱️ 10 min

**What you'll see**: A web app that changes theme color dynamically without code changes or container rebuilds.

**Kubernetes concepts**:
- ConfigMaps for externalized configuration
- Volume mounts for file-based config
- Pod restart to pick up new values

**Quick run**:
```bash
cd Dynamic-Theme-App
docker build -t dynamic-theme-app:latest -f ./app/Dockerfile ./app
kind load docker-image dynamic-theme-app:latest
kubectl apply -f ./k8s/configmap-deployment.yaml
kubectl apply -f ./k8s/service.yaml
kubectl port-forward -n dynamic-theme-demo svc/theme-app-service 8080:80
```
Then open `http://localhost:8080` in your browser. Edit the ConfigMap and restart to see the color change instantly.

**Learn more**: [Dynamic-Theme-App/README.md](Dynamic-Theme-App/README.md)

---

### 2️⃣ Multi-Replica-Web-Server — Scaling & Load Balancing ⏱️ 15 min

**What you'll see**: Multiple replicas of the same app behind a load balancer. Requests are distributed evenly; killing one pod automatically spawns a replacement.

**Kubernetes concepts**:
- Deployment replicas for horizontal scaling
- ClusterIP Service for load balancing
- In-cluster traffic distribution (iptables + kube-proxy)
- High availability through automatic pod replacement

**Quick run**:
```bash
cd Multi-Replica-Web-Server
docker build -t multi-replica-app:latest ./app
kind load docker-image multi-replica-app:latest
kubectl apply -n multi-replica-web -f ./k8s/deployment.yaml
kubectl apply -n multi-replica-web -f ./k8s/service.yaml
kubectl get pods -n multi-replica-web -w  # Watch in real-time
```

In another terminal, send requests from inside the cluster:
```bash
for i in {1..20}; do 
  kubectl run curl-test-$i -n multi-replica-web --rm -i --image=curlimages/curl --restart=Never -- \
    curl -s http://web-server-service/ 2>/dev/null | grep -o '"pod_name":"[^"]*"'
done | sort | uniq -c
```

You'll see traffic distributed across all 5 replicas!

**Learn more**: [Multi-Replica-Web-Server/README.md](Multi-Replica-Web-Server/README.md)

---

### 3️⃣ Health-Check-Demo — Liveness & Readiness Probes ⏱️ 10 min

**What you'll see**: Toggle a health endpoint to unhealthy, watch Kubernetes detect the failure via probes, and automatically restart the pod.

**Kubernetes concepts**:
- Liveness probes for detecting dead containers
- Readiness probes for traffic routing
- Automatic pod restart on failure
- Health-driven resilience

**Quick run**:
```bash
cd Health-Check-Demo
docker build -t health-check-app:latest -f ./app/Dockerfile ./app
kind load docker-image health-check-app:latest
kubectl apply -f ./k8s/deployment.yaml
kubectl apply -f ./k8s/service.yaml
kubectl port-forward -n health-check-demo svc/health-check-service 8080:80
```

In another terminal:
```bash
curl http://localhost:8080/health  # Should return healthy

# Toggle health to unhealthy
curl -X POST http://localhost:8080/toggle-health

# Watch the pod restart (in a 3rd terminal)
kubectl get pods -n health-check-demo -w
```

Within 10 seconds, the pod will restart and automatically recover!

**Learn more**: [Health-Check-Demo/README.md](Health-Check-Demo/README.md)

---

### 4️⃣ Chaos-Monkey — Self-Healing at Scale ⏱️ 12 min

**What you'll see**: Continuously delete pods from the command line while a web app never goes down. Kubernetes replaces each deleted pod instantly.

**Kubernetes concepts**:
- Deployment self-healing
- Service continuity during pod churn
- Replica controller ensuring desired state
- Observability through events and logs

**Quick run**:
```bash
cd Chaos-Monkey
docker build -t chaos-monkey-app:latest -f ./app/Dockerfile ./app
kind load docker-image chaos-monkey-app:latest
kubectl apply -f ./k8s/deployment.yaml
kubectl apply -f ./k8s/service.yaml

# Terminal 1: Watch pods in real-time
kubectl get pods -l app=chaos-monkey -w

# Terminal 2: Watch logs
kubectl logs -f -l app=chaos-monkey

# Terminal 3: Run chaos script (delete pods randomly every 5 seconds)
chmod +x ./chaos/chaos-monkey.sh
./chaos/chaos-monkey.sh --namespace default --label app=chaos-monkey --interval 5

# Terminal 4: Port-forward and verify service never stops
kubectl port-forward svc/chaos-monkey-service 9090:80
curl http://127.0.0.1:9090/  # Run repeatedly—always works!
```

**Learn more**: [Chaos-Monkey/README.md](Chaos-Monkey/README.md)

---

### 5️⃣ Resource-Limiter — Requests, Limits & Quotas ⏱️ 12 min

**What you'll see**: Allocate memory until the pod hits limits, triggers throttling, health checks fail, and Kubernetes restarts it. Shows resource governance in action.

**Kubernetes concepts**:
- Resource requests (minimum needed)
- Resource limits (maximum allowed)
- CPU throttling under load
- OOMKilled events when limits are exceeded
- Namespace ResourceQuota for multi-tenant governance

**Quick run**:
```bash
cd Resource-Limiter
docker build -t memory-limiter-app:latest -f ./app/Dockerfile ./app
kind load docker-image memory-limiter-app:latest
kubectl apply -f ./k8s/deployment.yaml
kubectl apply -f ./k8s/service.yaml
kubectl apply -f ./k8s/resource-quota.yaml

# Terminal 1: Port-forward
kubectl port-forward -n resource-limiter svc/memory-limiter-service 8080:80

# Terminal 2: Watch pods restart
kubectl get pods -n resource-limiter -w

# Terminal 3: Trigger allocations
for i in {1..6}; do 
  echo "=== Allocation $i ==="
  curl -X POST http://localhost:8080/allocate?mb=50
  sleep 3
done
```

Watch the pod memory grow, health fail, and pod restart count increment!

**Learn more**: [Resource-Limiter/README.md](Resource-Limiter/README.md)

---

### 6️⃣ Config-Hot-Reloader — Dynamic Configuration Reloading ⏱️ 12 min

**What you'll see**: Edit a ConfigMap and watch the app reload configuration **without pod restart**. Requests keep flowing while config updates happen instantly.

**Kubernetes concepts**:
- ConfigMap volume mounting
- File watching for dynamic updates (Python `watchdog`)
- Zero-downtime config changes
- Thread-safe state management
- Kubernetes file propagation timing

**Quick run**:
```bash
cd Config-Hot-Reloader
docker build -t config-hot-reloader:latest -f ./app/Dockerfile ./app
kind load docker-image config-hot-reloader:latest
kubectl apply -f ./k8s/namespace.yaml
kubectl apply -f ./k8s/configmap.yaml
kubectl apply -f ./k8s/deployment.yaml
kubectl apply -f ./k8s/service.yaml
kubectl port-forward -n config-hot-reloader svc/config-reloader-service 8080:80
```

In another terminal, watch logs:
```bash
kubectl logs -f -n config-hot-reloader deployment/config-reloader
```

Edit the config:
```bash
kubectl edit configmap app-config -n config-hot-reloader
# Change environment to "staging", debug_mode to true, etc.
# Save and exit
```

Watch the logs show the reload happen instantly, then verify:
```bash
curl http://localhost:8080/config | jq '.reload_count'  # Incremented!
```

**Pod never restarted!**

**Learn more**: [Config-Hot-Reloader/README.md](Config-Hot-Reloader/README.md)

---

### 7️⃣ Secure-API-Proxy — Secrets & Security ⏱️ 8 min

**What you'll see**: A proxy that enforces API key authentication (from a Secret) and forwards to an upstream URL (from ConfigMap). Shows secure credential management.

**Kubernetes concepts**:
- Secrets for sensitive data (API keys, passwords)
- ConfigMap for non-sensitive config
- Environment variables from Secrets
- Secure configuration patterns

**Quick run**:
```bash
cd Secure-API-Proxy
docker build -t secure-api-proxy:latest -f ./app/Dockerfile ./app
kind load docker-image secure-api-proxy:latest
kubectl apply -f ./k8s/secret.yaml
kubectl apply -f ./k8s/configmap.yaml
kubectl apply -f ./k8s/deployment.yaml
kubectl apply -f ./k8s/service.yaml

# Port-forward
kubectl port-forward -n secure-api-proxy deploy/secure-api-proxy 8080:8080

# Test with correct key (should work)
curl -H "X-API-KEY: demo-secret-key" http://localhost:8080/get

# Test with wrong key (should fail with 401)
curl -H "X-API-KEY: wrong" http://localhost:8080/get
```

**Learn more**: [Secure-API-Proxy/README.md](Secure-API-Proxy/README.md)

---

## 📊 Concept Map — Which Demo Teaches What?

| Kubernetes Concept | Demo(s) |
|---|---|
| **Configuration Management** | Dynamic-Theme-App, Config-Hot-Reloader, Secure-API-Proxy |
| **Scaling & Load Balancing** | Multi-Replica-Web-Server |
| **Health & Self-Healing** | Health-Check-Demo, Chaos-Monkey |
| **Resource Governance** | Resource-Limiter |
| **Secrets & Security** | Secure-API-Proxy |
| **High Availability** | Multi-Replica-Web-Server, Chaos-Monkey |
| **Observability** | Chaos-Monkey, Resource-Limiter, Config-Hot-Reloader |
| **Zero-Downtime Updates** | Config-Hot-Reloader |

---

## ⏱️ Suggested Demo Flow (30–60 minutes)

**For a 30-minute demo:**
1. **Dynamic-Theme-App** (5 min) — Quick visual win: change colors live
2. **Multi-Replica-Web-Server** (10 min) — Show load balancing and redundancy
3. **Health-Check-Demo** (10 min) — Show automatic recovery
4. **Resource-Limiter** (5 min) — Quick governance overview

**For a 45-minute presentation:**
1. **Dynamic-Theme-App** (5 min) — Config decoupling
2. **Config-Hot-Reloader** (10 min) — Zero-downtime config updates (WOW factor!)
3. **Multi-Replica-Web-Server** (12 min) — Replicas + load balancing + logs
4. **Health-Check-Demo** (10 min) — Probes + automatic restart
5. **Resource-Limiter** (8 min) — Governance + throttling

**For a 60-minute deep-dive:**
1. **Dynamic-Theme-App** (5 min) — Config decoupling
2. **Config-Hot-Reloader** (12 min) — Zero-downtime reload (deep dive into file watching)
3. **Multi-Replica-Web-Server** (12 min) — Replicas + load balancing + iptables routing
4. **Health-Check-Demo** (10 min) — Probes + automatic restart
5. **Chaos-Monkey** (10 min) — Self-healing at scale
6. **Resource-Limiter** (8 min) — Governance + throttling + OOMKilled
7. **Secure-API-Proxy** (5 min) — Secrets management

---

## 🚀 What Clients Will Understand

After these demos, your clients will see:

✅ **Kubernetes automates infrastructure** — No manual pod management  
✅ **Configuration is separate from code** — Change config without rebuilding  
✅ **Apps are highly available** — Automatic healing and scaling  
✅ **Resources are governed** — Limits and quotas prevent runaway consumption  
✅ **Credentials stay secure** — Secrets are never in code  
✅ **Load is distributed** — Multiple replicas share traffic  
✅ **Observability is built-in** — Logs and probes reveal everything  

---

## 📚 For Deeper Learning

Each project has:
- **README.md** — High-level overview and concepts
- **PROCEDURE.md** — Step-by-step walkthrough
- **app/** — Source code you can inspect
- **k8s/** — Kubernetes manifests you can study

---

## 💡 Pro Tips for Presenters

1. **Pre-build images** — Run `docker build` and `kind load` before the demo to save time.
2. **Use multiple terminals** — Show logs, pod watch, and requests in parallel terminals so clients see everything happening in real-time.
3. **Pause and explain** — After each "action," pause to explain what Kubernetes just did (e.g., "The liveness probe failed twice, so Kubernetes restarted the container").
4. **Let clients ask questions** — These are small, safe environments; encourage hands-on exploration.
5. **Show the YAML** — Point to the Deployment/Service manifests to show how Kubernetes is configured (`kubectl get deployment -o yaml`).

---

## 🆘 Troubleshooting Quick Reference

| Issue | Fix |
|---|---|
| Port-forward fails | Ensure pod is running: `kubectl get pods -n <namespace>` |
| Image pull fails | Reload image: `kind load docker-image <image-name>` |
| Pod pending | Check resource availability: `kubectl describe pod <pod>` |
| Health endpoint unreachable | Verify service exists: `kubectl get svc -n <namespace>` |

---

**Ready? Pick a demo and run the commands above. Good luck!** 🎉
