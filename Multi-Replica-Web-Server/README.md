# Multi-Replica Web Server — Kubernetes Load Balancing Demo

See how a Kubernetes Service spreads traffic across 5 replicas, which pod handled your request, and why port-forwarding shows only one.

---

## 🎯 What This Project Teaches

In real-world applications, you don't run just ONE copy of your server. Instead, you run **multiple copies** (replicas) and let Kubernetes decide which copy handles each request. This project shows you:

1. **Replicas** — How to run 5 copies of the same app
2. **Load Balancing** — How Kubernetes spreads traffic evenly across replicas
3. **Pod Identity** — How to identify which replica is serving your request
4. **Observability** — How to use logs to see traffic distribution
5. **High Availability** — What happens if one replica crashes (Kubernetes restarts it)

---

## 🏗️ Project Structure

```
Multi-Replica-Web-Server/
├── app/
│   ├── app.py              # Simple Flask web server
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Container image definition
├── k8s/
│   ├── deployment.yaml     # 5 replicas of the web server
│   └── service.yaml        # Load balancer for traffic distribution
├── README.md               # This file
└── PROCEDURE.md            # Step-by-step instructions
```

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Build and Load the Docker Image

```bash
cd /home/testuser/Documents/Practise/Multi-Replica-Web-Server
docker build -t multi-replica-app:latest ./app
kind load docker-image multi-replica-app:latest
```

### Step 2: Deploy to Kubernetes (in the correct namespace)

```bash
kubectl apply -n multi-replica-web -f ./k8s/deployment.yaml
kubectl apply -n multi-replica-web -f ./k8s/service.yaml
```

### Step 3: Verify All 5 Replicas Are Running

```bash
kubectl get pods -n multi-replica-web
```

You should see **5 pods** all in `Running` status:
```
NAME                                    READY   STATUS    RESTARTS   AGE
web-server-deployment-xxxxx-aaaaa       1/1     Running   0          10s
web-server-deployment-xxxxx-bbbbb       1/1     Running   0          10s
web-server-deployment-xxxxx-ccccc       1/1     Running   0          10s
web-server-deployment-xxxxx-ddddd       1/1     Running   0          10s
web-server-deployment-xxxxx-eeeee       1/1     Running   0          10s
```

### Step 4: Test Load Balancing (In-Cluster)

**Important:** `kubectl port-forward` connects to a single pod, so it won't show load balancing. To see real traffic distribution, send requests from inside the cluster:

```bash
# Terminal 1: Watch logs from all replicas
kubectl logs -f -n multi-replica-web -l app=web-server
```

```bash
# Terminal 2: Send 20 requests from inside cluster
for i in {1..20}; do 
  kubectl run curl-test-$i -n multi-replica-web --rm -i --image=curlimages/curl --restart=Never -- \
    curl -s http://web-server-service/ 2>/dev/null | grep -o '"pod_name":"[^"]*"' | cut -d'"' -f4
done
```

You'll see different pod names in the output, and logs from all 5 replicas!

### Step 5: Optional - Port-Forward for Quick Testing

**Note:** This connects to one pod only (no load balancing visible):

```bash
kubectl port-forward -n multi-replica-web svc/web-server-service 8080:80
```

Then test:
```bash
curl http://localhost:8080/info | jq .
```

### Step 6: Watch Logs in Real-Time

In another terminal, watch logs from ALL replicas:

```bash
kubectl logs -f -n multi-replica-web -l app=web-server
```

You'll see requests logged from different replicas like:
```
[2026-01-11T14:45:23.123456] Request received by web-server-deployment-xxxxx-aaaaa (Replica aaaaa)
[2026-01-11T14:45:23.234567] Request received by web-server-deployment-xxxxx-ccccc (Replica ccccc)
[2026-01-11T14:45:23.345678] Request received by web-server-deployment-xxxxx-bbbbb (Replica bbbbb)
```

---

## 📚 Understanding the Concepts

### What is a Replica?

A **replica** is a complete copy of your app. If you have 5 replicas, you have 5 independent containers running the same code.

**Why?**
- **Load Balancing** — Requests are spread across all 5, so no single replica gets overloaded
- **High Availability** — If one replica crashes, 4 others keep running
- **Updates** — You can update replicas one-by-one without downtime

### How Does Kubernetes Route Requests?

1. **Service** creates a single IP address (`web-server-service`)
2. When you send a request to the Service, Kubernetes **randomly picks** one of the 5 replicas
3. The request goes to that replica
4. The next request goes to a **different** replica (likely)

### Traffic Distribution Pattern

```
Your requests to Service
        ↓
    [Load Balancer]
        ↓
    ┌───┬───┬───┬───┬───┐
    ↓   ↓   ↓   ↓   ↓   ↓
   Pod1 Pod2 Pod3 Pod4 Pod5  (5 Replicas)
```

### Example: 10 Requests Distribution

```
Request 1  → Pod 3
Request 2  → Pod 1
Request 3  → Pod 5
Request 4  → Pod 2
Request 5  → Pod 4
Request 6  → Pod 1
Request 7  → Pod 3
Request 8  → Pod 5
Request 9  → Pod 2
Request 10 → Pod 4
```

Notice it's **random**, not round-robin!

---

## 🔍 Observing Traffic Distribution

### Method 1: In-Cluster Testing (Recommended - Shows Real Load Balancing)

**This is the correct way to see load balancing in action!**

```bash
# Terminal 1: Watch logs from all replicas
kubectl logs -f -n multi-replica-web -l app=web-server
```

```bash
# Terminal 2: Send 20 requests from inside the cluster
for i in {1..20}; do 
  kubectl run curl-test-$i -n multi-replica-web --rm -i --image=curlimages/curl --restart=Never -- \
    curl -s http://web-server-service/ 2>/dev/null | grep -o '"pod_name":"[^"]*"' | cut -d'"' -f4
done
```

**Expected output:** You'll see 5 different pod names distributed across the 20 requests!

Example distribution:
```
5 requests → web-server-deployment-xxxxx-aaaaa
4 requests → web-server-deployment-xxxxx-bbbbb
4 requests → web-server-deployment-xxxxx-ccccc
4 requests → web-server-deployment-xxxxx-ddddd
3 requests → web-server-deployment-xxxxx-eeeee
```

### Method 2: Count Distribution

```bash
# Send requests and count per replica
for i in {1..20}; do 
  kubectl run test-$i -n multi-replica-web --rm -i --image=curlimages/curl --restart=Never -- \
    curl -s http://web-server-service/ 2>/dev/null | grep -o '"pod_name":"[^"]*"' | cut -d'"' -f4
done | sort | uniq -c
```

### Method 3: Port-Forward Testing (Single Pod Only)

⚠️ **Important:** `kubectl port-forward` to a Service connects to ONE backend pod. You won't see load balancing with this method, but it's useful for quick testing.

```bash
# Terminal 1: Port-forward (connects to single pod)
kubectl port-forward -n multi-replica-web svc/web-server-service 8080:80
```

```bash
# Terminal 2: Send requests (all go to same pod)
curl http://localhost:8080/info | jq '.pod_name'
```

You'll see the **same pod name** every time because port-forward maintains a direct connection to one pod.

---

## 🛠️ Endpoints

### GET `/`
Returns pod info and confirms replica received your request.

```bash
curl http://localhost:8080/ | jq .
```

**Response:**
```json
{
  "message": "Hello from Replica aaaaa!",
  "pod_name": "web-server-deployment-xxxxx-aaaaa",
  "pod_ip": "10.244.0.10",
  "node_name": "kind-control-plane",
  "hostname": "web-server-deployment-xxxxx-aaaaa",
  "replica_id": "aaaaa",
  "timestamp": "2026-01-11T14:45:23.123456"
}
```

### GET `/info`
Detailed info about the replica handling your request.

```bash
curl http://localhost:8080/info | jq .
```

### GET `/health`
Health check for Kubernetes probes.

```bash
curl http://localhost:8080/health
```

### GET `/load`
Simulates 1 second of work (useful for observing request handling).

```bash
curl http://localhost:8080/load
```

---

## 📊 What You'll Observe

### Log Format

Every request is logged with:
```
[TIMESTAMP] Request received by POD_NAME (Replica REPLICA_ID)
```

Example:
```
[2026-01-11T14:45:23.123456] Request received by web-server-deployment-xxxxx-aaaaa (Replica aaaaa)
[2026-01-11T14:45:24.234567] Request received by web-server-deployment-xxxxx-ccccc (Replica ccccc)
[2026-01-11T14:45:25.345678] Request received by web-server-deployment-xxxxx-bbbbb (Replica bbbbb)
```

### What Demonstrates Load Balancing?

1. **Different replicas handling requests** — Each request goes to a different pod
2. **Logs from all 5 replicas** — Over time, you see logs from all 5 pods
3. **Roughly equal distribution** — Each replica handles ~20% of total requests

---

## 🔧 Configuration

### Change Number of Replicas

Edit `k8s/deployment.yaml`, line 11:

```yaml
spec:
  replicas: 5  # Change this number
```

Then apply:
```bash
kubectl apply -f ./k8s/deployment.yaml
```

### Change Load Balancing Strategy

Edit `k8s/service.yaml`:

```yaml
sessionAffinity: None        # Random per request (current)
# OR
sessionAffinity: ClientIP    # Sticky: same client → same replica
```

**Difference:**
- `None` — Each request is random
- `ClientIP` — Your IP always routes to the same replica (useful for sessions)

---

## 🧹 Cleanup

Remove everything:

```bash
# Delete deployment and service
kubectl delete namespace multi-replica-web

# Verify
kubectl get pods -n multi-replica-web
```

You should get:
```
Error from server (NotFound): namespaces "multi-replica-web" not found
```

---

## 📝 Next Steps

1. **Watch logs while making requests** — See real-time traffic distribution
2. **Scale up/down replicas** — Edit deployment.yaml and observe
3. **Kill a pod** — See Kubernetes automatically restart it
4. **Sticky sessions** — Change sessionAffinity and observe behavior

---

## 🎓 Learning Outcomes

After this project, you'll understand:

✅ How to run multiple replicas of an app  
✅ How Kubernetes load-balances traffic  
✅ How to identify which replica served your request  
✅ How to observe traffic distribution in logs  
✅ Why replicas improve availability  
✅ How Kubernetes keeps replicas healthy  

---

## 📖 For Step-by-Step Instructions

See **[PROCEDURE.md](PROCEDURE.md)** for detailed commands and explanations.

---

**Happy learning!** 🎉
