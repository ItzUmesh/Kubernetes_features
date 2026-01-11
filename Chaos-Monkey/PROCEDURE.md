# PROCEDURE (Manual) — Run / Test / Observe / Stop

This file describes a step-by-step procedure for beginners to deploy, test, and run the Chaos Monkey app on a local kind (Kubernetes in Docker) cluster.

---

## Prerequisites (manual checks)

Before you start, verify that your environment is set up correctly:

1. Confirm `kubectl` is installed and your context points to a kind cluster:
   ```bash
   kubectl cluster-info
   kubectl config current-context
   ```
   The context should be something like `kind-<cluster-name>` (e.g., `kind-kind`).

2. Confirm you can run basic kubectl commands:
   ```bash
   kubectl get nodes
   kubectl get namespaces
   ```

3. Confirm your kind cluster is running:
   ```bash
   kind get clusters
   ```
   If you see no clusters, create one:
   ```bash
   kind create cluster
   ```

4. Ensure Docker is installed and running:
   ```bash
   docker --version
   docker ps
   ```

---

## 1) BUILD — Build the container image locally

### Step A — Navigate to the project root
```bash
cd <path-to-Chaos-Monkey-repo>
```

### Step B — Build the Docker image
```bash
docker build -t chaos-monkey-app:latest -f ./app/Dockerfile ./app
```

Verify the image was built:
```bash
docker images | grep chaos-monkey-app
```

You should see `chaos-monkey-app:latest` in the list.

---

## 2) LOAD — Make the image available to your kind cluster

### Step A — Confirm your kind cluster name
```bash
kind get clusters
```
Note the cluster name (e.g., `kind` or `umesh-cluster`).

### Step B — Load the image into your kind cluster
Replace `<cluster-name>` with the name from Step A:
```bash
kind load docker-image chaos-monkey-app:latest --name <cluster-name>
```

Example:
```bash
kind load docker-image chaos-monkey-app:latest --name kind
```

You should see a message like:
```
Image: "chaos-monkey-app:latest" ... loading...
```

**Important Note:**
The `deployment.yaml` file already includes `imagePullPolicy: IfNotPresent`. This tells Kubernetes to use the image already present on the node instead of trying to pull it from Docker Hub. This is essential for kind to work.

---

## 3) DEPLOY — Deploy the app to your cluster

### Step A — Apply the Kubernetes deployment
```bash
kubectl apply -f ./k8s/deployment.yaml
```

### Step B — Apply the service
```bash
kubectl apply -f ./k8s/service.yaml
```

### Step C — Verify pods are created and running
```bash
kubectl get pods -l app=chaos-monkey
```

Wait 10-15 seconds, then run the command again. All three pods should show:
```
READY   STATUS
1/1     Running
```

If pods are stuck in `ErrImagePull` or `ImagePullBackOff`, see the **Troubleshooting** section below.

---

## 4) TEST — Verify the app is serving traffic

### Step A — Check pod logs
```bash
kubectl logs -l app=chaos-monkey --tail=50
```

You should see Flask startup messages. If there are errors, check individual pod logs:
```bash
kubectl logs <pod-name>
```

### Step B — Port-forward to the service
In one terminal, run:
```bash
kubectl port-forward svc/chaos-monkey-service 8080:80
```

### Step C — Test the endpoint
In a different terminal, run:
```bash
curl http://127.0.0.1:8080/
```

You should see a JSON response like:
```json
{"hostname":"chaos-monkey-deployment-654f86cd76-h794g"}
```

The hostname shows which pod is serving the request. This confirms the app is working.

---

## 5) OBSERVE — Watch Chaos Monkey delete and recreate pods

### Step A — Start the chaos script (in a new terminal)
```bash
chmod +x ./chaos/chaos-monkey.sh
./chaos/chaos-monkey.sh --namespace default --label app=chaos-monkey --interval 5
```

The script will print:
```
Starting Chaos Monkey: namespace=default label=app=chaos-monkey interval=5s
Press Ctrl-C to stop.
Deleting pod: <pod-name>
```

Keep this terminal open to watch the deletions.

### Step B — Watch pod recreation (in another terminal)
```bash
kubectl get pods -l app=chaos-monkey -w
```

You will see pods being deleted and new ones being created immediately. The `-w` flag means "watch," so the output updates in real-time.

### Step C — Record your observations
- Which pod names are deleted?
- How long until a replacement appears?
- Do the pod restart counts increase in kubectl?
- Run `curl http://127.0.0.1:8080/` multiple times to see different pod hostnames serving your requests.

---

## 6) STOP — Clean up and stop the test

### Step A — Stop the chaos script
Press `Ctrl-C` in the chaos-monkey.sh terminal.

### Step B — Optional: Delete all Chaos Monkey resources
If you want to clean up the deployment, service, and pods:
```bash
kubectl delete deployment chaos-monkey-deployment
kubectl delete svc chaos-monkey-service
```

This stops all chaos-monkey pods and removes the service.

---

## Troubleshooting

### Pods stuck in `ErrImagePull` or `ImagePullBackOff`

**Symptom:** Pods remain in `ErrImagePull` or `ImagePullBackOff` state for more than 30 seconds.

**Root causes and solutions:**

1. **Image not loaded into kind:**
   - Run:
     ```bash
     docker images | grep chaos-monkey-app
     ```
   - If no image is listed, build it:
     ```bash
     docker build -t chaos-monkey-app:latest -f ./app/Dockerfile ./app
     ```
   - Then load it:
     ```bash
     kind load docker-image chaos-monkey-app:latest --name <cluster-name>
     ```

2. **Wrong cluster name:**
   - Confirm your kind cluster name:
     ```bash
     kind get clusters
     ```
   - Make sure you used the correct name in the `kind load` command.
   - Check your kubectl context:
     ```bash
     kubectl config current-context
     ```

3. **Image not present on cluster nodes:**
   - Verify the image is on the node:
     ```bash
     docker images | grep chaos-monkey-app
     ```
   - If not present, reload:
     ```bash
     kind load docker-image chaos-monkey-app:latest --name <cluster-name>
     ```

4. **Deployment.yaml has wrong image name or missing imagePullPolicy:**
   - Check the deployment:
     ```bash
     kubectl get deployment chaos-monkey-deployment -o yaml | grep -A 2 "image:"
     ```
   - It should show:
     ```yaml
     image: chaos-monkey-app:latest
     imagePullPolicy: IfNotPresent
     ```
   - If not, verify k8s/deployment.yaml has both settings and re-apply:
     ```bash
     kubectl apply -f ./k8s/deployment.yaml
     ```

5. **Pods keep crashing after starting:**
   - Check pod logs:
     ```bash
     kubectl logs <pod-name>
     ```
   - If you see port binding errors, the Flask app may not be starting. Verify the Dockerfile and app.py are correct.

### chaos-monkey.sh not deleting pods properly

**Symptom:** The script runs but pods are not being deleted, or errors appear.

**Solution:**
- Ensure the script has execute permissions:
  ```bash
  chmod +x ./chaos/chaos-monkey.sh
  ```
- Verify pods exist with the correct label:
  ```bash
  kubectl get pods -l app=chaos-monkey
  ```
- Run the script with verbose output:
  ```bash
  bash -x ./chaos/chaos-monkey.sh --namespace default --label app=chaos-monkey --interval 5
  ```

### kubectl port-forward connection refused

**Symptom:** `curl http://127.0.0.1:8080/` returns "Connection refused" or times out.

**Solution:**
- Ensure port-forward is still running in its terminal:
  ```bash
  kubectl port-forward svc/chaos-monkey-service 8080:80
  ```
- In a different terminal, test:
  ```bash
  curl -v http://127.0.0.1:8080/
  ```
- If still failing, check if pods are running:
  ```bash
  kubectl get pods -l app=chaos-monkey
  ```

### Full reset if nothing works

If you continue to have issues, do a complete reset:

1. Delete old deployments and pods:
   ```bash
   kubectl delete deployment chaos-monkey-deployment
   kubectl delete svc chaos-monkey-service
   ```

2. Delete and recreate the kind cluster:
   ```bash
   kind delete cluster --name <cluster-name>
   kind create cluster --name <cluster-name>
   ```

3. Rebuild and reload the image:
   ```bash
   docker build -t chaos-monkey-app:latest -f ./app/Dockerfile ./app
   kind load docker-image chaos-monkey-app:latest --name <cluster-name>
   ```

4. Re-apply manifests:
   ```bash
   kubectl apply -f ./k8s/deployment.yaml
   kubectl apply -f ./k8s/service.yaml
   ```

5. Verify pods are running:
   ```bash
   kubectl get pods -l app=chaos-monkey
   ```

---

## Summary

This procedure demonstrates the complete lifecycle of the Chaos Monkey application:

1. **Build:** Package the Flask app as a Docker image.
2. **Load:** Make the image available to your local kind cluster.
3. **Deploy:** Run the app in Kubernetes with a Deployment and Service.
4. **Test:** Verify the app responds to HTTP requests.
5. **Observe:** Watch Kubernetes automatically recreate pods when the chaos script deletes them.
6. **Stop:** Clean up resources when done.

The Chaos Monkey script simulates pod failures, and Kubernetes responds by creating replacement pods—demonstrating the self-healing capability of Kubernetes.

For more details on each component, see [README.md](README.md).

---

**This procedure is intentionally manual: perform each step, inspect outputs, and confirm expected state before moving on.**
