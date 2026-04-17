# 🏷️ Label-Selector-Lab — Step-by-Step Procedure

---

## Step 1: Build the Docker Image

```bash
cd Label-Selector-Lab
docker build -t label-selector-app:latest ./app
```

> The app is a tiny HTTP server. It reads its labels from env vars injected by
> the Kubernetes **Downward API** and exposes them at `GET /`.

---

## Step 2: Load the Image into kind

```bash
kind load docker-image label-selector-app:latest
```

> If you use a different cluster (e.g. minikube), use `minikube image load` instead.

---

## Step 3: Deploy to Kubernetes

```bash
kubectl apply -f k8s/deployments.yaml
```

This creates:
- A dedicated namespace `label-selector-lab`
- 4 Deployments → **6 pods** total, each with a unique label combination

---

## Step 4: Verify Pods Are Running

```bash
kubectl get pods -n label-selector-lab --show-labels
```

Expected output (6 pods, all `Running`):

```
NAME                              READY   STATUS    LABELS
frontend-prod-xxxx-xxxxx          1/1     Running   app=...,env=prod,tier=frontend,team=alpha
frontend-prod-xxxx-xxxxx          1/1     Running   app=...,env=prod,tier=frontend,team=alpha
frontend-dev-xxxx-xxxxx           1/1     Running   app=...,env=dev,tier=frontend,team=beta
backend-prod-xxxx-xxxxx           1/1     Running   app=...,env=prod,tier=backend,team=alpha
backend-prod-xxxx-xxxxx           1/1     Running   app=...,env=prod,tier=backend,team=alpha
backend-dev-xxxx-xxxxx            1/1     Running   app=...,env=dev,tier=backend,team=beta
```

---

## Step 5: Install the Python kubernetes Client

```bash
# pip is not available via yum on RHEL 9 — bootstrap it first, then install:
curl -s https://bootstrap.pypa.io/get-pip.py | python3 - --user
python3 -m pip install kubernetes --user
```

---

## Step 6: Run the Interactive Selector Demo

```bash
python3 selector.py
```

You'll see a menu like this:

```
══════════════════════════════════════════════════════════
  ☸️  Label-Selector-Lab  —  Pod Filter Demo
══════════════════════════════════════════════════════════

Choose a label selector:
   1. All pods in namespace
   2. env=prod  (all production pods)
   3. env=dev   (all development pods)
   4. tier=frontend  (all frontend pods)
   ...
  11. env=dev,tier=backend    (dev-backend)
  12. Custom selector (type your own)
   0. Exit
```

Try each option and observe how Kubernetes narrows down the pod list.

---

## Step 7: Try One-Shot CLI Queries

```bash
# All pods
python3 selector.py --all

# Production pods only
python3 selector.py --selector "env=prod"

# Production frontend pods
python3 selector.py --selector "env=prod,tier=frontend"

# Team alpha pods
python3 selector.py --selector "team=alpha"
```

---

## Step 8: Verify Labels Directly with kubectl

These kubectl commands mirror exactly what `selector.py` does internally:

```bash
kubectl get pods -n label-selector-lab -l env=prod
kubectl get pods -n label-selector-lab -l env=prod,tier=frontend
kubectl get pods -n label-selector-lab -l team=alpha
```

---

## Step 9: Curl a Pod to See Its Label Data

```bash
# Port-forward any pod
kubectl port-forward -n label-selector-lab \
  $(kubectl get pod -n label-selector-lab -l env=prod,tier=frontend -o name | head -1) \
  8080:8080

# In another terminal
curl http://localhost:8080/
```

Example response:
```json
{
  "message": "Label-Selector-Lab pod is running!",
  "pod_name": "frontend-prod-5d8c7f4b6-xk9z2",
  "namespace": "label-selector-lab",
  "labels": {
    "env": "prod",
    "tier": "frontend",
    "team": "alpha"
  }
}
```

---

## Step 10: Cleanup

```bash
kubectl delete namespace label-selector-lab
```
