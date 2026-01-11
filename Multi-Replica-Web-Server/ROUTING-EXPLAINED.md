# Kubernetes Load Balancing — Technical Deep Dive

This document explains **exactly how** Kubernetes routes traffic to multiple replicas and where the load balancing happens.

---

## 🎯 The Three Components of Routing

### 1. **Service Definition** (Configuration)

Location: [`k8s/service.yaml`](k8s/service.yaml)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-server-service
  namespace: multi-replica-web
spec:
  type: ClusterIP
  selector:
    app: web-server          # ← Routes to pods with this label
  ports:
    - protocol: TCP
      port: 80               # ← Service listens on port 80
      targetPort: 5000       # ← Forwards to pod port 5000
  sessionAffinity: None      # ← Random distribution (no sticky sessions)
```

**What it does:**
- Creates a virtual IP (ClusterIP)
- Defines which pods receive traffic (via `selector`)
- Maps Service port to pod port
- Configures load balancing behavior

---

### 2. **kube-proxy** (Implementation)

Runs on every Kubernetes node and implements the Service routing.

**How it works:**
1. Watches the Kubernetes API for Service and Endpoint changes
2. Creates **iptables rules** (or uses IPVS mode) on each node
3. Traffic to the Service IP is intercepted by these rules
4. Rules perform **random selection** among healthy pods
5. Traffic is **DNAT'ed** (destination NAT) directly to the chosen pod

**Check kube-proxy mode:**
```bash
kubectl logs -n kube-system -l k8s-app=kube-proxy | grep "Using iptables Proxier"
```

---

### 3. **Endpoints** (Backend Registry)

Kubernetes automatically creates an Endpoints object that lists all pod IPs matching the Service selector.

**View your endpoints:**
```bash
kubectl get endpoints -n multi-replica-web web-server-service
```

**Expected output:**
```
NAME                 ENDPOINTS                                                        AGE
web-server-service   10.244.0.60:5000,10.244.0.61:5000,10.244.0.62:5000 + 2 more...   29m
```

**Detailed view:**
```bash
kubectl describe endpoints -n multi-replica-web web-server-service
```

**Output:**
```
Name:         web-server-service
Namespace:    multi-replica-web
Subsets:
  Addresses:          10.244.0.60,10.244.0.61,10.244.0.62,10.244.0.63,10.244.0.64
  NotReadyAddresses:  <none>
  Ports:
    Name     Port  Protocol
    ----     ----  --------
    <unset>  5000  TCP
```

---

## 🔍 Your Actual Cluster Configuration

### Service Details

```bash
kubectl get svc -n multi-replica-web web-server-service -o wide
```

**Output:**
```
NAME                 TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE   SELECTOR
web-server-service   ClusterIP   10.96.39.165   <none>        80/TCP    29m   app=web-server
```

**Key Information:**
- **ClusterIP**: `10.96.39.165` (the virtual IP clients connect to)
- **Port**: `80` (what clients use)
- **Selector**: `app=web-server` (matches pods with this label)

---

### Pod to IP Mapping

```bash
kubectl get pods -n multi-replica-web -o wide
```

**Your 5 replicas:**
```
NAME                                     READY   STATUS    IP             NODE
web-server-deployment-86b8bb7db4-5q9j2   1/1     Running   10.244.0.60    kind-control-plane
web-server-deployment-86b8bb7db4-gplst   1/1     Running   10.244.0.61    kind-control-plane
web-server-deployment-86b8bb7db4-hqld7   1/1     Running   10.244.0.62    kind-control-plane
web-server-deployment-86b8bb7db4-sdvd5   1/1     Running   10.244.0.63    kind-control-plane
web-server-deployment-86b8bb7db4-rtnt2   1/1     Running   10.244.0.64    kind-control-plane
```

**Backend Pool:**
```
10.244.0.60:5000  →  web-server-deployment-86b8bb7db4-5q9j2
10.244.0.61:5000  →  web-server-deployment-86b8bb7db4-gplst
10.244.0.62:5000  →  web-server-deployment-86b8bb7db4-hqld7
10.244.0.63:5000  →  web-server-deployment-86b8bb7db4-sdvd5
10.244.0.64:5000  →  web-server-deployment-86b8bb7db4-rtnt2
```

---

## 🧱 The Actual iptables Rules

### View iptables Rules

```bash
docker exec kind-control-plane iptables-save | grep "web-server-service"
```

### Entry Point Rule

When traffic arrives at the Service IP (`10.96.39.165:80`), this rule matches:

```iptables
-A KUBE-SERVICES -d 10.96.39.165/32 -p tcp --dport 80 -j KUBE-SVC-63H3HC53DASTWFBN
```

**Translation:** Traffic to `10.96.39.165:80` jumps to the Service chain `KUBE-SVC-63H3HC53DASTWFBN`.

---

### Load Balancing Chain

The Service chain `KUBE-SVC-63H3HC53DASTWFBN` randomly selects one of 5 pods:

```iptables
# Chain: KUBE-SVC-63H3HC53DASTWFBN (load balancing logic)

# Rule 1: 20% probability → Pod 1 (10.244.0.60:5000)
-A KUBE-SVC-63H3HC53DASTWFBN \
   -m comment --comment "multi-replica-web/web-server-service -> 10.244.0.60:5000" \
   -m statistic --mode random --probability 0.20000000019 \
   -j KUBE-SEP-HU22O7KC5VBP3V6G

# Rule 2: 25% probability → Pod 2 (10.244.0.61:5000)
-A KUBE-SVC-63H3HC53DASTWFBN \
   -m comment --comment "multi-replica-web/web-server-service -> 10.244.0.61:5000" \
   -m statistic --mode random --probability 0.25000000000 \
   -j KUBE-SEP-PHL6EH3Y5JZKNDW2

# Rule 3: 33.33% probability → Pod 3 (10.244.0.62:5000)
-A KUBE-SVC-63H3HC53DASTWFBN \
   -m comment --comment "multi-replica-web/web-server-service -> 10.244.0.62:5000" \
   -m statistic --mode random --probability 0.33333333349 \
   -j KUBE-SEP-XQ54E5ECTRZUX6VV

# Rule 4: 50% probability → Pod 4 (10.244.0.63:5000)
-A KUBE-SVC-63H3HC53DASTWFBN \
   -m comment --comment "multi-replica-web/web-server-service -> 10.244.0.63:5000" \
   -m statistic --mode random --probability 0.50000000000 \
   -j KUBE-SEP-WBBLDCZTM5EO32FO

# Rule 5: 100% probability (fallthrough) → Pod 5 (10.244.0.64:5000)
-A KUBE-SVC-63H3HC53DASTWFBN \
   -m comment --comment "multi-replica-web/web-server-service -> 10.244.0.64:5000" \
   -j KUBE-SEP-KRKXVEXU6DSBNBQB
```

---

### Probability Math Explained

Each pod gets **exactly 20% of traffic**:

| Rule | Probability | Math | Result |
|------|-------------|------|--------|
| Pod 1 | 0.20 | 20% directly | **20%** |
| Pod 2 | 0.25 | (100% - 20%) × 25% = 80% × 25% | **20%** |
| Pod 3 | 0.33 | (100% - 40%) × 33.33% = 60% × 33.33% | **20%** |
| Pod 4 | 0.50 | (100% - 60%) × 50% = 40% × 50% | **20%** |
| Pod 5 | 1.00 | (100% - 80%) × 100% = 20% × 100% | **20%** |

**Algorithm:**
1. Try Pod 1: 20% chance → if selected, done
2. Try Pod 2: 25% of remaining 80% → if selected, done
3. Try Pod 3: 33.33% of remaining 60% → if selected, done
4. Try Pod 4: 50% of remaining 40% → if selected, done
5. Pod 5: Gets the remaining 20%

This ensures **perfect equal distribution**!

---

### DNAT (Destination NAT) Rules

Each `KUBE-SEP-*` chain performs DNAT to rewrite the destination to the selected pod:

```iptables
# Pod 1: Rewrite destination to 10.244.0.60:5000
-A KUBE-SEP-HU22O7KC5VBP3V6G \
   -p tcp \
   -m comment --comment "multi-replica-web/web-server-service" \
   -j DNAT --to-destination 10.244.0.60:5000

# Pod 2: Rewrite destination to 10.244.0.61:5000
-A KUBE-SEP-PHL6EH3Y5JZKNDW2 \
   -p tcp \
   -m comment --comment "multi-replica-web/web-server-service" \
   -j DNAT --to-destination 10.244.0.61:5000

# Pod 3: Rewrite destination to 10.244.0.62:5000
-A KUBE-SEP-XQ54E5ECTRZUX6VV \
   -p tcp \
   -m comment --comment "multi-replica-web/web-server-service" \
   -j DNAT --to-destination 10.244.0.62:5000

# Pod 4: Rewrite destination to 10.244.0.63:5000
-A KUBE-SEP-WBBLDCZTM5EO32FO \
   -p tcp \
   -m comment --comment "multi-replica-web/web-server-service" \
   -j DNAT --to-destination 10.244.0.63:5000

# Pod 5: Rewrite destination to 10.244.0.64:5000
-A KUBE-SEP-KRKXVEXU6DSBNBQB \
   -p tcp \
   -m comment --comment "multi-replica-web/web-server-service" \
   -j DNAT --to-destination 10.244.0.64:5000
```

---

## 🌊 Complete Traffic Flow

### Request Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│  Client sends request to: web-server-service:80         │
│  DNS resolves to ClusterIP: 10.96.39.165                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Packet hits node's network stack                       │
│  iptables PREROUTING chain                              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  KUBE-SERVICES chain matches:                           │
│  -d 10.96.39.165/32 -p tcp --dport 80                   │
│  Jump to → KUBE-SVC-63H3HC53DASTWFBN                    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Load Balancing Chain (KUBE-SVC-63H3HC53DASTWFBN)       │
│  Random selection with equal probability (20% each):    │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 20% Pod1 │  │ 20% Pod2 │  │ 20% Pod3 │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│  ┌──────────┐  ┌──────────┐                            │
│  │ 20% Pod4 │  │ 20% Pod5 │                            │
│  └──────────┘  └──────────┘                            │
│                                                          │
│  Randomly selects one → KUBE-SEP-* chain                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  DNAT Rule (example: KUBE-SEP-HU22O7KC5VBP3V6G)         │
│  Rewrites packet destination:                           │
│  FROM: 10.96.39.165:80                                  │
│  TO:   10.244.0.60:5000                                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Packet routed to selected pod                          │
│  Pod IP: 10.244.0.60                                    │
│  Pod Port: 5000                                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Flask app receives request                             │
│  Logs: "Request received by pod-5q9j2"                  │
│  Returns response                                       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Response travels back through NAT                      │
│  Source rewritten: 10.244.0.60:5000 → 10.96.39.165:80  │
│  Client receives response                               │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 What Happens When Pods Change?

### Pod Added/Removed

1. **Deployment controller** creates/deletes pods
2. **Kubelet** reports pod status to API server
3. **Endpoints controller** updates Endpoints object
4. **kube-proxy** watches Endpoints changes
5. **kube-proxy** updates iptables rules:
   - Adds new DNAT rules for new pods
   - Removes rules for deleted pods
   - Recalculates probabilities for equal distribution

### Example: Scaling from 5 to 3 replicas

**Before (5 replicas):**
```iptables
-A KUBE-SVC-... --probability 0.20 -j POD1  # 20%
-A KUBE-SVC-... --probability 0.25 -j POD2  # 20%
-A KUBE-SVC-... --probability 0.33 -j POD3  # 20%
-A KUBE-SVC-... --probability 0.50 -j POD4  # 20%
-A KUBE-SVC-... -j POD5                     # 20%
```

**After (3 replicas):**
```iptables
-A KUBE-SVC-... --probability 0.33333 -j POD1  # 33.33%
-A KUBE-SVC-... --probability 0.50000 -j POD2  # 33.33%
-A KUBE-SVC-... -j POD3                        # 33.33%
```

kube-proxy **automatically recalculates** to maintain equal distribution!

---

## 🚫 Why Port-Forward Doesn't Show Load Balancing

### Port-Forward Path

```
kubectl port-forward command
         ↓
   kubectl (client)
         ↓
   Kubernetes API Server
         ↓
   Direct connection to ONE specific pod
   (bypasses Service, bypasses iptables)
         ↓
   Pod receives all traffic
```

**Key differences:**
- ❌ No Service IP involved
- ❌ No iptables rules executed
- ❌ No load balancing
- ❌ All requests go to the same pod
- ✅ Good for debugging individual pods
- ✅ Good for local development

### In-Cluster Request Path

```
In-cluster pod/process
         ↓
   DNS lookup: web-server-service
   Returns: 10.96.39.165
         ↓
   Connect to 10.96.39.165:80
         ↓
   iptables intercepts traffic
         ↓
   KUBE-SERVICES chain
         ↓
   Load balancing (random selection)
         ↓
   DNAT to selected pod
         ↓
   Traffic distributed across all 5 pods
```

**Key differences:**
- ✅ Uses Service IP
- ✅ iptables rules execute
- ✅ Load balancing works
- ✅ Requests distributed across all replicas

---

## 🧪 Verify Routing Works

### 1. Check Service and Endpoints

```bash
# Service details
kubectl get svc -n multi-replica-web web-server-service -o wide

# Endpoints (backend pod IPs)
kubectl describe endpoints -n multi-replica-web web-server-service

# Verify all 5 pods are listed
```

### 2. Check iptables Rules

```bash
# View all rules for your service
docker exec kind-control-plane iptables-save | grep "web-server-service"

# View the load balancing chain
docker exec kind-control-plane iptables-save | grep "KUBE-SVC-63H3HC53DASTWFBN" -A 10
```

### 3. Test Load Distribution

```bash
# Send 20 requests from inside cluster
for i in {1..20}; do 
  kubectl run curl-test-$i -n multi-replica-web --rm -i \
    --image=curlimages/curl --restart=Never -- \
    curl -s http://web-server-service/ 2>/dev/null | \
    grep -o '"pod_name":"[^"]*"' | cut -d'"' -f4
done | sort | uniq -c
```

**Expected result:**
```
      4 web-server-deployment-86b8bb7db4-5q9j2
      4 web-server-deployment-86b8bb7db4-gplst
      4 web-server-deployment-86b8bb7db4-hqld7
      4 web-server-deployment-86b8bb7db4-rtnt2
      4 web-server-deployment-86b8bb7db4-sdvd5
```

All 5 replicas should get approximately equal traffic! ✅

---

## 📚 Key Takeaways

### Where Routing Happens

| Component | Role | Location |
|-----------|------|----------|
| **Service** | Configuration | Kubernetes API (YAML manifest) |
| **Endpoints** | Backend registry | Kubernetes API (auto-generated) |
| **kube-proxy** | Implementation | Runs on every node |
| **iptables** | Packet manipulation | Linux kernel (each node) |

### Load Balancing Algorithm

- **Type**: Random selection with equal probability
- **Implementation**: iptables statistic module
- **Distribution**: Each pod gets 1/N of traffic (N = number of replicas)
- **Session affinity**: None (can be changed to ClientIP for sticky sessions)

### Traffic Never Hits the Service

The Service IP (`10.96.39.165`) is **virtual**:
- No process listens on this IP
- iptables intercepts packets destined for it
- Traffic is **DNAT'ed directly to pods**
- Pods never see the Service IP in the packet

### Debugging Commands

```bash
# Check Service
kubectl get svc -n multi-replica-web

# Check Endpoints (backend pods)
kubectl get endpoints -n multi-replica-web

# Check iptables rules
docker exec kind-control-plane iptables-save | grep "web-server-service"

# Test load distribution
for i in {1..20}; do kubectl run test-$i -n multi-replica-web --rm -i \
  --image=curlimages/curl --restart=Never -- \
  curl -s http://web-server-service/ 2>/dev/null | grep pod_name; done
```

---

## 🎓 Further Learning

### Related Kubernetes Concepts

- **Service Types**: ClusterIP (internal), NodePort (external), LoadBalancer (cloud)
- **Session Affinity**: Sticky sessions based on client IP
- **IPVS Mode**: Alternative to iptables (better performance for many endpoints)
- **Headless Services**: Direct pod-to-pod communication without load balancing
- **EndpointSlices**: Scalable alternative to Endpoints for large clusters

### Advanced Topics

- **kube-proxy modes**: iptables, IPVS, userspace
- **Network policies**: Control traffic flow between pods
- **Service mesh** (Istio, Linkerd): Advanced traffic management
- **External load balancers**: Cloud provider integrations

---

**Last Updated:** January 11, 2026  
**Cluster:** kind (local Kubernetes)  
**Service:** web-server-service (multi-replica-web namespace)
