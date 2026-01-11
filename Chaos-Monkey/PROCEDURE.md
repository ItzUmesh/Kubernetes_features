
# PROCEDURE (Manual) — Run / Test / Observe / Stop

This file describes a manual, step-by-step procedure for beginners. It assumes you will perform each action by hand and inspect results before moving to the next step.

## Prerequisites (manual checks)
- Confirm `kubectl` is installed and your context points to the intended cluster:
  ```bash
  kubectl cluster-info
  kubectl config current-context
  ```
- Confirm you can run simple commands against the cluster:
  ```bash
  kubectl get nodes
  kubectl get namespaces
  ```
- If you plan to build locally, ensure `docker` (or `kind`/`minikube`) is installed and usable.

---

## 1) Run — build and deploy (manual steps)

### Step A — Build the container image locally
```bash
cd <path-to-repo-root>
docker build -t chaos-monkey-app:latest -f ./app/Dockerfile ./app
# Verify image exists locally
docker images | grep chaos-monkey-app
```

### Step B — Make the image available to your cluster

This step makes sure your Kubernetes cluster can find and use the image you just built. Follow the instructions that match your setup:

#### If you are using kind (Kubernetes in Docker):
1. Make sure you have already built the image as shown in Step A.
2. Run this command to load your local image into the kind cluster:
  ```bash
  kind load docker-image chaos-monkey-app:latest
  ```
  This tells kind to copy your image into its own internal Docker registry, so your pods can use it.

#### If you are using minikube:
1. You need to build the image inside minikube’s Docker environment. Run these commands:
  ```bash
  eval $(minikube docker-env)
  docker build -t chaos-monkey-app:latest ./app
  ```
  The first command switches your terminal to use minikube’s Docker. The second command builds the image inside minikube, so it’s available to your cluster.

#### If you are using a remote cluster (like a cloud provider):
1. You need to upload ("push") your image to a container registry that your cluster can access (like Docker Hub or Google Container Registry).
2. Tag your image for the registry. For example, if using Docker Hub:
  ```bash
  docker tag chaos-monkey-app:latest <your-dockerhub-username>/chaos-monkey-app:latest
  ```
3. Push the image to the registry:
  ```bash
  docker push <your-dockerhub-username>/chaos-monkey-app:latest
  ```
4. Edit your deployment.yaml file and set the image field to the full registry path (e.g., `<your-dockerhub-username>/chaos-monkey-app:latest`).

If you are not sure which method to use, ask your instructor or check how your cluster was set up.

### Step C — Deploy manifests and confirm deployment creation
```bash
kubectl apply -f ./k8s/deployment.yaml
kubectl apply -f ./k8s/service.yaml
# Verify pods begin to appear
kubectl get pods -l app=chaos-monkey
```
Pause and inspect the pod list and events. If pods are not starting, run `kubectl describe pod <pod>` and resolve errors before continuing.

---

## 2) Test — manual verification the app is serving

### Step A — Check pod logs for startup errors
```bash
kubectl logs <pod-name>
kubectl logs -l app=chaos-monkey --tail=100
```

### Step B — Access the service manually
- If your Service is ClusterIP:
  ```bash
  kubectl port-forward svc/chaos-monkey-service 8080:80
  # In another terminal
  curl http://127.0.0.1:8080/
  ```
- If NodePort or LoadBalancer, use the external address and port.
Confirm the response contains the `hostname` field so you can identify the serving pod.

---

## 3) Observe — manually run chaos and watch behavior

### Step A — Start the chaos script
```bash
chmod +x ./chaos/chaos-monkey.sh
./chaos/chaos-monkey.sh --namespace default --label app=chaos-monkey --interval 5
```
Keep this terminal open so you can observe which pod names are being deleted.

### Step B — Watch pod lifecycle and events
```bash
kubectl get pods -l app=chaos-monkey -w
kubectl get events -n default --sort-by=.metadata.creationTimestamp
```
When a pod is deleted by the script, confirm a new pod is created by the Deployment. Record:
- Which pod names were deleted
- How long until replacements appeared
- Any error events in `kubectl describe pod <new-pod>`

---

## 4) Stop — end manual test and clean up

### Step A — Stop the chaos script
- Press Ctrl-C in the script terminal.

### Step B — Verify Deployment stabilizes
```bash
kubectl get pods -l app=chaos-monkey
kubectl describe deployment chaos-monkey-deployment
```

### Step C — Optional cleanup
```bash
kubectl delete -f ./k8s/deployment.yaml
kubectl delete -f ./k8s/service.yaml
```

---

## Troubleshooting (manual checks)

### Image pull errors (`ErrImagePull` / `ImagePullBackOff`)
- Run:
  ```bash
  kubectl describe pod <pod-name>
  ```
- If you see:
  - `pull access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed`
    - The image is not present in the registry or is private.
    - Solution: For kind/minikube, load the image as above. For remote clusters, push the image to a registry and update the deployment manifest.
  - `unauthorized`: create an `imagePullSecret` and reference it in the deployment YAML.
  - `manifest unknown`: verify image name and tag are correct in `deployment.yaml` and that the image exists in the registry.

### Networking/DNS issues
- Try:
  ```bash
  kubectl exec -it <pod> -- nslookup registry.example.com
  # or
  kubectl exec -it <pod> -- curl -v registry.example.com
  ```

### General advice
- If you are uncertain, record commands and outputs and seek help; do not proceed until the core issue (image pull or crash) is resolved.

---

**This procedure is intentionally manual: perform each step, inspect outputs, and confirm expected state before moving on.**
