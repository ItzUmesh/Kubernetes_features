# Multi-Replica Web Server — Complete Setup Procedure

This document provides **step-by-step instructions** to deploy and test the multi-replica load-balancing project.

---

## 📋 Prerequisites

Verify you have:

1. **Docker** installed
   ```bash
   docker --version
   ```

2. **Kubernetes (kind)** running locally
   ```bash
   kubectl cluster-info
   ```

3. **Working directory** set up
   ```bash
   cd /home/testuser/Documents/Practise/Multi-Replica-Web-Server
   ls -la  # Should show: app/, k8s/, README.md, PROCEDURE.md
   ```

---

## 🚀 Step 1: Build Docker Image

Build the Docker image for the web server application.

```bash
cd /home/testuser/Documents/Practise/Multi-Replica-Web-Server
docker build -t multi-replica-app:latest ./app
```

**Expected output:**
```
Sending build context to Docker daemon  2.048kB
Step 1/6 : FROM python:3.11-slim
 ---> a1234567890a
Step 2/6 : WORKDIR /app
 ---> Running in b2c3d4e5f6g7
 ---> Removed intermediate container b2c3d4e5f6g7
 ---> a2b3c4d5e6f7
Step 3/6 : COPY requirements.txt .
 ---> a3b4c5d6e7f8
Step 4/6 : RUN pip install -r requirements.txt
 ---> a4b5c6d7e8f9
Step 5/6 : COPY app.py .
 ---> a5b6c7d8e9f0
Step 6/6 : CMD ["python", "app.py"]
 ---> a6b7c8d9e0f1
Successfully built a6b7c8d9e0f1
Successfully tagged multi-replica-app:latest
```

### Verify image was created

```bash
docker images | grep multi-replica-app
```

**Expected output:**
```
multi-replica-app      latest      a6b7c8d9e0f1   2 minutes ago   145MB
```

---

## 🎯 Step 2: Load Image into Kind

Load the Docker image into your kind cluster so it's available for Kubernetes.

```bash
kind load docker-image multi-replica-app:latest
```

**Expected output:**
```
Image: "multi-replica-app:latest" with ID "sha256:a6b7c8d9e0f1..." loaded into kind cluster "kind"
```

### Why this step?

Kind runs Kubernetes in a container. Docker images on your host aren't automatically available inside the cluster. We must explicitly load them.

---

## 🚀 Step 3: Create Kubernetes Namespace

Create a dedicated namespace for this project.

```bash
kubectl create namespace multi-replica-web
```

**Expected output:**
```
namespace/multi-replica-web created
```

### Verify namespace was created

```bash
kubectl get namespaces
```

**Expected output:**
```
NAME                 STATUS   AGE
default              Active   5d
kube-node-lease      Active   5d
kube-public          Active   5d
kube-system          Active   5d
multi-replica-web    Active   10s
```

---

## 📦 Step 4: Deploy the Application

Deploy the Deployment and Service manifests to Kubernetes.

### Deploy the Deployment (5 replicas)

```bash
kubectl apply -n multi-replica-web -f ./k8s/deployment.yaml
```

**Expected output:**
```
deployment.apps/web-server-deployment created
```

### Deploy the Service (load balancer)

```bash
kubectl apply -n multi-replica-web -f ./k8s/service.yaml
```

**Expected output:**
```
service/web-server-service created
```

---

## ✅ Step 5: Verify All 5 Replicas Are Running

Check that all 5 pods are in the `Running` state.

```bash
kubectl get pods -n multi-replica-web
```

**Expected output:**
```
NAME                                      READY   STATUS    RESTARTS   AGE
web-server-deployment-7d8b9c4f6e-2k3m4    1/1     Running   0          15s
web-server-deployment-7d8b9c4f6e-5n6o7    1/1     Running   0          15s
web-server-deployment-7d8b9c4f6e-8p9q0    1/1     Running   0          15s
web-server-deployment-7d8b9c4f6e-1r2s3    1/1     Running   0          15s
web-server-deployment-7d8b9c4f6e-4t5u6    1/1     Running   0          15s
```

**All should show:**
- `READY: 1/1` ✅
- `STATUS: Running` ✅

### Troubleshooting

If pods show `ImagePullBackOff`:

```bash
# Check events
kubectl describe pod <pod-name> -n multi-replica-web

# Solution: Make sure image was loaded with 'kind load docker-image'
kind load docker-image multi-replica-app:latest
```

---

## 🧪 Step 6: Test Load Balancing (In-Cluster Method)

**This is the correct way to observe load balancing!** Requests from inside the cluster go through the Service's load balancer.

### Start Watching Logs

In a **separate terminal**, watch logs from all replicas:

```bash
kubectl logs -f -n multi-replica-web -l app=web-server
```

**Expected output:**
```
[2026-01-11T15:35:01.971515] Request received by web-server-deployment-xxxxx-aaaaa (Replica xxxxx-aaaaa)
[2026-01-11T15:35:14.139748] Request received by web-server-deployment-xxxxx-bbbbb (Replica xxxxx-bbbbb)
[2026-01-11T15:35:19.282045] Request received by web-server-deployment-xxxxx-ccccc (Replica xxxxx-ccccc)
```

Notice requests from **different replicas**!

### Send Test Requests

In another terminal, send 20 requests from inside the cluster:

```bash
for i in {1..20}; do 
  kubectl run curl-test-$i -n multi-replica-web --rm -i --image=curlimages/curl --restart=Never -- \
    curl -s http://web-server-service/ 2>/dev/null | grep -o '"pod_name":"[^"]*"' | cut -d'"' -f4
done
```

**Expected output:**
```
web-server-deployment-xxxxx-aaaaa
web-server-deployment-xxxxx-bbbbb
web-server-deployment-xxxxx-aaaaa
web-server-deployment-xxxxx-ccccc
web-server-deployment-xxxxx-ddddd
web-server-deployment-xxxxx-eeeee
...
```

You'll see **5 different pod names** distributed across the 20 requests!

### Count Distribution

```bash
echo "Distribution count:"
for i in {1..20}; do 
  kubectl run test-$i -n multi-replica-web --rm -i --image=curlimages/curl --restart=Never -- \
    curl -s http://web-server-service/ 2>/dev/null | grep -o '"pod_name":"[^"]*"' | cut -d'"' -f4
done | sort | uniq -c | sort -rn
```

**Expected output:**
```
      5 web-server-deployment-xxxxx-aaaaa
      4 web-server-deployment-xxxxx-bbbbb
      4 web-server-deployment-xxxxx-ccccc
      4 web-server-deployment-xxxxx-ddddd
      3 web-server-deployment-xxxxx-eeeee
```

Perfect! All 5 replicas handled requests with roughly equal distribution.

---

## 🌐 Step 7: Optional - Port-Forward for Quick Testing

⚠️ **Important Note:** `kubectl port-forward` to a Service connects to a **single backend pod**. You will NOT see load balancing with this method, but it's useful for quick testing of individual endpoints.

**Keep this command running in a separate terminal:**

```bash
kubectl port-forward -n multi-replica-web svc/web-server-service 8080:80
```

**Expected output:**
```
Forwarding from 127.0.0.1:8080 -> 5000
Forwarding from [::1]:8080 -> 5000
```

### Test Single Request

```bash
curl http://localhost:8080/info | jq .
```

**Expected output:**
```json
{
  "hostname": "web-server-deployment-xxxxx-aaaaa",
  "node_name": "kind-control-plane",
  "pod_ip": "10.244.0.60",
  "pod_name": "web-server-deployment-xxxxx-aaaaa",
  "replica_id": "web-server-deployment-xxxxx-aaaaa",
  "timestamp": "2026-01-11T15:35:01.971515"
}
```

**Note:** With port-forward, you'll see the **same pod** every time because the connection tunnels to one specific pod.

---

## 📊 Step 8: Understanding Load Balancing vs Port-Forward

### Why Port-Forward Doesn't Show Load Balancing

`kubectl port-forward` creates a **direct tunnel** to a single backend pod:
```
Your laptop → port-forward → ONE specific pod
```

All requests through `localhost:8080` go to the same pod.

### How Real Load Balancing Works

When requests come from **inside the cluster**, they go through the Service's load balancer:
```
In-cluster request → Service (load balancer) → Randomly picks from 5 pods
```

That's why Step 6's in-cluster test shows distribution!

---

## 📈 Step 9: Observe Traffic Distribution with Logs

If you completed Step 6, you already saw this in action! This section provides more details.

**Watch logs** (if not already running):

```bash
kubectl logs -f -n multi-replica-web -l app=web-server
```

This command:
- `-f` = Follow (stream logs in real-time)
- `-n multi-replica-web` = Look in this namespace
- `-l app=web-server` = Label selector (all pods with this label)

**Expected output from in-cluster requests:**
```
[2026-01-11T15:35:01.971515] Request received by web-server-deployment-xxxxx-aaaaa (Replica xxxxx-aaaaa)
[2026-01-11T15:35:14.139748] Request received by web-server-deployment-xxxxx-bbbbb (Replica xxxxx-bbbbb)
[2026-01-11T15:35:19.282045] Request received by web-server-deployment-xxxxx-ccccc (Replica xxxxx-ccccc)
[2026-01-11T15:35:29.190877] Request received by web-server-deployment-xxxxx-ddddd (Replica xxxxx-ddddd)
[2026-01-11T15:35:39.251217] Request received by web-server-deployment-xxxxx-eeeee (Replica xxxxx-eeeee)
```

Notice:
- ✅ **Different replicas** appear in the logs
- ✅ **Each request goes to a different pod**
- ✅ This proves **load balancing is working!**

---

## 🔄 Step 10: Continuous Traffic Test

Let's create continuous traffic and watch load balancing in action.

### Terminal 1: Send continuous requests (every 2 seconds)

```bash
while true; do
  curl -s http://localhost:8080/ | jq '.replica_id'
  sleep 2
done
```

### Terminal 2: Watch logs (in real-time)

```bash
kubectl logs -f -n multi-replica-web -l app=web-server
```

**What you'll observe:**
- Logs appearing continuously
- Logs from **different replicas** appearing in sequence
- Each pod serving approximately equal number of requests

**This demonstrates:**
- ✅ Load balancing distributes requests
- ✅ All replicas are handling traffic
- ✅ No single replica is overloaded

---

## 🔧 Step 11: Advanced — Test Replica Restart

Kubernetes automatically restarts crashed replicas. Let's test this.

### Kill a pod

```bash
# Get a pod name
POD=$(kubectl get pods -n multi-replica-web -o jsonpath='{.items[0].metadata.name}')
echo "Killing pod: $POD"

# Delete the pod
kubectl delete pod $POD -n multi-replica-web
```

**Expected output:**
```
pod "web-server-deployment-7d8b9c4f6e-2k3m4" deleted
```

### Verify it restarts automatically

```bash
kubectl get pods -n multi-replica-web
```

**Watch the output:**
```
NAME                                      READY   STATUS              RESTARTS   AGE
web-server-deployment-7d8b9c4f6e-2k3m4    0/1     ContainerCreating   0          2s   ← NEW!
web-server-deployment-7d8b9c4f6e-5n6o7    1/1     Running             0          5m
web-server-deployment-7d8b9c4f6e-8p9q0    1/1     Running             0          5m
web-server-deployment-7d8b9c4f6e-1r2s3    1/1     Running             0          5m
web-server-deployment-7d8b9c4f6e-4t5u6    1/1     Running             0          5m
```

Wait a few seconds:

```bash
kubectl get pods -n multi-replica-web
```

**Result:**
```
NAME                                      READY   STATUS    RESTARTS   AGE
web-server-deployment-7d8b9c4f6e-2k3m4    1/1     Running   0          10s    ← Restarted!
web-server-deployment-7d8b9c4f6e-5n6o7    1/1     Running   0          5m
web-server-deployment-7d8b9c4f6e-8p9q0    1/1     Running   0          5m
web-server-deployment-7d8b9c4f6e-1r2s3    1/1     Running   0          5m
web-server-deployment-7d8b9c4f6e-4t5u6    1/1     Running   0          5m
```

**Key takeaway:**
- We deleted one pod
- Kubernetes **automatically created a replacement**
- Still 5 replicas running
- No downtime! ✅

This is why replicas provide **high availability**.

---

## 🔧 Step 12: Advanced — Scale Replicas Up/Down

Kubernetes makes it easy to scale replicas.

### Scale to 10 replicas

```bash
kubectl scale deployment web-server-deployment --replicas=10 -n multi-replica-web
```

**Expected output:**
```
deployment.apps/web-server-deployment scaled
```

### Verify 10 pods are running

```bash
kubectl get pods -n multi-replica-web
```

**Expected output:**
```
NAME                                      READY   STATUS    RESTARTS   AGE
web-server-deployment-7d8b9c4f6e-2k3m4    1/1     Running   0          6m
web-server-deployment-7d8b9c4f6e-5n6o7    1/1     Running   0          6m
web-server-deployment-7d8b9c4f6e-8p9q0    1/1     Running   0          6m
web-server-deployment-7d8b9c4f6e-1r2s3    1/1     Running   0          6m
web-server-deployment-7d8b9c4f6e-4t5u6    1/1     Running   0          6m
web-server-deployment-7d8b9c4f6e-6x7y8    1/1     Running   0          30s   ← NEW
web-server-deployment-7d8b9c4f6e-9z0a1    1/1     Running   0          30s   ← NEW
web-server-deployment-7d8b9c4f6e-2b3c4    1/1     Running   0          30s   ← NEW
web-server-deployment-7d8b9c4f6e-5d6e7    1/1     Running   0          30s   ← NEW
web-server-deployment-7d8b9c4f6e-8f9g0    1/1     Running   0          30s   ← NEW
```

Now **10 replicas!** Kubernetes created 5 new pods automatically.

### Scale back to 5 replicas

```bash
kubectl scale deployment web-server-deployment --replicas=5 -n multi-replica-web
```

**Result:**
```
deployment.apps/web-server-deployment scaled
```

Kubernetes will **terminate 5 pods** to bring it back to 5 replicas.

---

## 🧹 Cleanup

When done with the project, clean everything up.

### Delete the namespace (removes all pods and services)

```bash
kubectl delete namespace multi-replica-web
```

**Expected output:**
```
namespace "multi-replica-web" deleted
```

### Verify deletion

```bash
kubectl get namespaces | grep multi-replica-web
```

**Expected output:**
```
(empty — namespace is gone)
```

### Optional: Delete Docker image

```bash
docker rmi multi-replica-app:latest
```

---

## 🎯 Summary of Key Concepts

### What You Just Learned

1. **Replicas** = Multiple identical copies of your app
2. **Service** = Single entry point that distributes requests
3. **Load Balancing** = Requests randomly distributed across replicas
4. **High Availability** = If one replica fails, others keep running
5. **Auto-Healing** = Kubernetes restarts failed pods automatically
6. **Scaling** = Easy to add/remove replicas without code changes

### Important Commands Reference

| Task | Command |
|------|---------|
| Build image | `docker build -t multi-replica-app:latest ./app` |
| Load to kind | `kind load docker-image multi-replica-app:latest` |
| Deploy | `kubectl apply -f ./k8s/*.yaml` |
| Port-forward | `kubectl port-forward -n multi-replica-web svc/web-server-service 8080:80` |
| Watch logs | `kubectl logs -f -n multi-replica-web -l app=web-server` |
| Scale | `kubectl scale deployment web-server-deployment --replicas=X -n multi-replica-web` |
| Delete | `kubectl delete namespace multi-replica-web` |

---

## 🐛 Troubleshooting

### Problem: Pods in `ImagePullBackOff`

**Cause:** Docker image not available in kind cluster

**Solution:**
```bash
kind load docker-image multi-replica-app:latest
```

### Problem: Connection refused on localhost:8080

**Cause:** Port-forward not running

**Solution:**
```bash
kubectl port-forward -n multi-replica-web svc/web-server-service 8080:80
```

(Keep this running in a dedicated terminal)

### Problem: Only seeing logs from one pod

**Cause:** Using pod name instead of label selector

**Solution:**
```bash
# DON'T use:
kubectl logs -f web-server-deployment-7d8b9c4f6e-2k3m4 -n multi-replica-web

# DO use:
kubectl logs -f -l app=web-server -n multi-replica-web
```

### Problem: Service not responding

**Cause:** Service might not have endpoints

**Debug:**
```bash
kubectl get svc -n multi-replica-web
kubectl get endpoints -n multi-replica-web
kubectl describe svc web-server-service -n multi-replica-web
```

---

## ✨ Next Steps

- **Experiment:** Scale to 3, 10, 20 replicas and watch logs
- **Observe:** See traffic distribution change with different replica counts
- **Test:** Kill pods and watch Kubernetes restart them
- **Learn:** Change `sessionAffinity` in service.yaml and observe behavior change

---

**Congratulations!** You now understand Kubernetes load balancing! 🎉
