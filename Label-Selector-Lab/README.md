# 🏷️ Label-Selector-Lab

> **Phase A — Project 4** of the [Kubernetes Feature-Lab](https://github.com/ItzUmesh/Kubernetes_features)

Use the Python Kubernetes client to **filter and list pods** based on custom labels — one of the most fundamental but powerful Kubernetes concepts.

---

## 🎯 What You'll Learn

- How to attach **custom labels** to pods via Deployment manifests
- How to use **label selectors** (`env=prod`, `tier=frontend`, etc.) to query pods
- How Kubernetes uses labels for **Service routing**, **scheduling**, and **access control**
- How to interact with the K8s API programmatically using the **Python `kubernetes` client**

---

## 🗂️ Project Structure

```
Label-Selector-Lab/
├── app/
│   ├── app.py            # Simple HTTP server that reports its own labels
│   ├── Dockerfile
│   └── requirements.txt
├── k8s/
│   └── deployments.yaml  # 4 deployments with different label combinations
├── selector.py           # ⭐ Main demo script — filter pods by label
├── PROCEDURE.md
└── README.md
```

---

## 🏷️ Label Matrix

Six pods are deployed across four deployments, each carrying three labels:

| Deployment       | `env`  | `tier`     | `team`  | Replicas |
|-----------------|--------|------------|---------|----------|
| `frontend-prod` | prod   | frontend   | alpha   | 2        |
| `frontend-dev`  | dev    | frontend   | beta    | 1        |
| `backend-prod`  | prod   | backend    | alpha   | 2        |
| `backend-dev`   | dev    | backend    | beta    | 1        |

---

## ⚡ Quick Start

```bash
# 1. Build the image
docker build -t label-selector-app:latest ./app

# 2. Load into kind
kind load docker-image label-selector-app:latest

# 3. Deploy all pods
kubectl apply -f k8s/deployments.yaml

# 4. Wait for pods to be ready
kubectl get pods -n label-selector-lab --watch

# 5. Install the Python kubernetes client
# (RHEL 9: pip is not in yum — bootstrap it first)
curl -s https://bootstrap.pypa.io/get-pip.py | python3 - --user
python3 -m pip install kubernetes --user

# 6. Run the interactive selector script
python3 selector.py
```

---

## 🔍 Example Queries

```bash
# List all pods
python3 selector.py --all

# Only production pods
python3 selector.py --selector "env=prod"

# Only production frontend pods
python3 selector.py --selector "env=prod,tier=frontend"

# All pods belonging to Team Alpha
python3 selector.py --selector "team=alpha"
```

---

## 🧹 Cleanup

```bash
kubectl delete namespace label-selector-lab
```

---

## 🗺️ Architecture Overview

The project has **two separate programs** that work together:

```
┌─────────────────────────────────────────────────────┐
│                   Kubernetes Cluster                 │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ frontend-prod│  │ frontend-dev │  ← Pods running  │
│  │ (×2 replicas)│  │ (×1 replica) │    app.py        │
│  └──────────────┘  └──────────────┘                 │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ backend-prod │  │ backend-dev  │                 │
│  │ (×2 replicas)│  │ (×1 replica) │                 │
│  └──────────────┘  └──────────────┘                 │
└───────────────────────────┬─────────────────────────┘
                            │  K8s API
                    ┌───────▼────────┐
                    │  selector.py   │  ← Runs on your machine
                    └────────────────┘
```

- **`app.py`** runs inside every pod and announces its own identity (name + labels).
- **`selector.py`** runs on your local machine and queries the K8s API to filter pods.

---

## 🔬 In-Depth Code Walkthrough

---

### Part 1 — `app/app.py` (The Pod Application)

A minimal HTTP server whose only job is to report **who it is** when queried.

#### How a pod knows its own labels — The Downward API

Kubernetes has a feature called the **Downward API** that lets a pod read its own
metadata (name, namespace, labels) and have it injected as environment variables at
runtime. In `deployments.yaml`:

```yaml
env:
- name: POD_NAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name   # K8s injects the real pod name here
- name: LABEL_ENV
  value: "prod"                  # we manually mirror the label value
```

`app.py` reads these at startup:

```python
POD_NAME  = os.environ.get("POD_NAME", "unknown")
LABEL_ENV = os.environ.get("LABEL_ENV", "unknown")
```

#### Endpoints

| Endpoint | Response |
|---|---|
| `GET /` | JSON with pod name, namespace, and all three labels |
| `GET /health` | `{"status": "healthy"}` — used by the K8s readiness probe |
| anything else | 404 |

#### The `PodInfoHandler` class

Extends Python's built-in `BaseHTTPRequestHandler`. When a request arrives,
`do_GET()` is called. It parses the URL path and delegates to `_send_json()` which:
1. Serialises the dict to JSON
2. Sets `Content-Type` and `Content-Length` headers
3. Writes the body to the TCP socket

#### Why is `log_message` overridden?

```python
def log_message(self, format, *args):
    pass  # silences "127.0.0.1 - GET / 200" noise on every health check
```

Python's built-in server prints an access log line for every request. Overriding
with `pass` suppresses it so pod logs stay clean.

---

### Part 2 — `k8s/deployments.yaml` (The Infrastructure)

One file — multiple YAML documents separated by `---` — that declares everything
needed in the cluster.

#### The Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: label-selector-lab
```

A namespace is an **isolation boundary** (like a folder). All 6 pods live inside
`label-selector-lab`, separated from other workloads.

#### Labels in two places — and why it matters

Each Deployment sets labels in **two distinct locations**:

```yaml
# 1. Labels on the Deployment object itself (organises Deployments)
metadata:
  labels:
    env: prod
    tier: frontend

# 2. Labels on every POD the Deployment creates (this is what selector.py queries)
spec:
  template:
    metadata:
      labels:
        app: label-selector-app
        env: prod
        tier: frontend
        team: alpha
```

`spec.selector.matchLabels` is how the **Deployment tracks its own pods**. It says:
_"I own any pod that has exactly these labels."_

```yaml
spec:
  selector:
    matchLabels:
      app: label-selector-app
      env: prod
      tier: frontend
```

#### The Readiness Probe

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 3
  periodSeconds: 5
```

Kubernetes calls `GET /health` every 5 seconds (after a 3s startup grace period).
If the response is not `200`, the pod is marked **Not Ready** and removed from
Service routing. This is why `app.py` has the `/health` endpoint.

---

### Part 3 — `selector.py` (The Demo Script)

The main demonstration tool. Uses the **official `kubernetes` Python client** to
talk to the K8s API server directly — exactly what `kubectl` does under the hood.

#### Step 1 — Load Credentials

```python
config.load_kube_config()      # reads ~/.kube/config on your laptop
# falls back to:
config.load_incluster_config() # reads a mounted ServiceAccount token if inside a pod
```

`~/.kube/config` contains the cluster address, your TLS certificate, and your
auth token. `load_kube_config()` reads it so the client knows where and how to
authenticate.

#### Step 2 — The API Client

```python
v1 = client.CoreV1Api()
```

The Kubernetes API is split into groups. `CoreV1Api` maps to `/api/v1` — the
**core group** containing Pods, Services, Namespaces, ConfigMaps, Secrets.
Other groups like `AppsV1Api` handle Deployments, StatefulSets, etc.

#### Step 3 — The Key API Call

```python
pods = v1.list_namespaced_pod(
    namespace=NAMESPACE,
    label_selector=label_selector,   # e.g. "env=prod,tier=frontend"
)
```

This sends an HTTP request to the cluster:

```
GET /api/v1/namespaces/label-selector-lab/pods?labelSelector=env%3Dprod%2Ctier%3Dfrontend
```

The API server does the filtering server-side — only matching pods come back.
This is the **exact same mechanism** that Services use internally to route traffic
to the right pods.

#### Step 4 — Parsing the Response

```python
for pod in pods.items:
    labels = pod.metadata.labels or {}   # dict of all labels on the pod
    phase  = pod.status.phase            # "Running", "Pending", "Failed" …
    node   = pod.spec.node_name          # which node it's scheduled on
```

`pods.items` is a list of `V1Pod` Python dataclasses that mirror the YAML structure:

| Attribute | Contains |
|---|---|
| `pod.metadata` | name, namespace, labels, annotations |
| `pod.status` | phase, conditions, container statuses |
| `pod.spec` | node name, containers, volumes |

#### Step 5 — CLI vs Interactive Mode

```python
# argparse: two mutually exclusive flags
group.add_argument("--selector", "-s", ...)  # one-shot with a specific selector
group.add_argument("--all", "-a", ...)        # one-shot, no filter

# No flags given → launch the interactive menu
if args.selector:
    list_pods(args.selector)
elif args.all:
    list_pods(None)
else:
    interactive_menu()           # default when you just run "python3 selector.py"
```

`add_mutually_exclusive_group()` ensures `--selector` and `--all` cannot be
passed together — `argparse` raises an error automatically.

---

## 🔑 The Core Kubernetes Concept — Label Selectors

Labels are **key=value metadata** attached to any Kubernetes object. They are
not interpreted by Kubernetes — you define them freely.

A label selector is a **filter query** against those key=value pairs:

| Selector | Meaning |
|---|---|
| `env=prod` | pods where the `env` label equals `prod` |
| `env=prod,tier=frontend` | pods where **both** conditions are true (AND logic) |
| `team=alpha` | pods where `team` equals `alpha` |
| *(empty)* | all pods in the namespace |

This same mechanism powers many core Kubernetes features:

| Feature | How it uses labels |
|---|---|
| **Service** | Routes traffic only to pods matching `selector:` |
| **Deployment** | Tracks which pods it owns via `matchLabels:` |
| **NetworkPolicy** | Applies firewall rules to pods matching `podSelector:` |
| **kubectl get pods -l** | What `selector.py` replicates in Python |
| **Node Affinity** | Schedules pods onto nodes matching a label |
