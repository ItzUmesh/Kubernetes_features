
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

This step makes sure your kind (Kubernetes in Docker) cluster can find and use the image you just built.

#### For kind (kindkube):
1. Make sure you have already built the image as shown in Step A:
  ```bash
  docker build -t chaos-monkey-app:latest -f ./app/Dockerfile ./app
  ```
2. Load your local image into the kind cluster:
  ```bash
  kind load docker-image chaos-monkey-app:latest --name umesh-cluster
  ```
  If your kind cluster has a custom name (not the default "kind"), specify it with:
  ```bash
  kind load docker-image chaos-monkey-app:latest --name <your-cluster-name>
  ```
  Replace <your-cluster-name> with the name shown by `kind get clusters` (e.g., umesh-cluster).
  This command copies your image into kind’s internal Docker registry, so your pods can use it. You only need to do this after building or rebuilding the image.

**Troubleshooting: Image not present locally**

If you see an error like:
```
ERROR: image: "chaos-monkey-app:latest" not present locally
```
It means you have not built the image yet, or the image name does not match.

1. Make sure you build the image with the exact name:
   ```bash
   docker build -t chaos-monkey-app:latest -f ./app/Dockerfile ./app
   ```
2. Then load it into your kind cluster as shown above.

**Note:** The image name must match in both the build and load commands. If you use a different name (e.g., chaos-monkey:latest), use that name in both places.

**Troubleshooting: 'no nodes found for cluster "kind"' error**

If you see this error, it means your kind cluster is not running or does not exist.

1. Check if any kind clusters exist:
  ```bash
  kind get clusters
  ```
  If nothing is listed, you need to create a cluster.
2. To create a new kind cluster, run:
  ```bash
  kind create cluster
  ```
  Wait for the cluster to be ready.
3. After the cluster is running, try loading the image again:
  ```bash
  kind load docker-image chaos-monkey-app:latest
  ```

If you need to delete and recreate the cluster for any reason:
```bash
kind delete cluster
kind create cluster
```



**Important:**
To prevent Kubernetes from always trying to pull the image from Docker Hub, make sure your deployment.yaml includes:

    imagePullPolicy: IfNotPresent

This line should be placed under the chaos-monkey container section, like this:

```yaml
containers:
  - name: chaos-monkey
    image: chaos-monkey-app:latest
    imagePullPolicy: IfNotPresent
    # ... other fields ...
```

This ensures Kubernetes uses the image you loaded into kind.

You can now continue to the next step to deploy your app to the cluster.

### Step C — Deploy manifests and confirm deployment creation
```bash
kubectl apply -f ./k8s/deployment.yaml
kubectl apply -f ./k8s/service.yaml
# Verify pods begin to appear
kubectl get pods -l app=chaos-monkey
```

Pause and inspect the pod list and events. If pods are not starting, run `kubectl describe pod <pod>` and resolve errors before continuing.

---

### Advanced troubleshooting: Persistent ImagePullBackOff

If you have followed all steps above and your pods are still stuck in ImagePullBackOff or ErrImagePull, try the following advanced steps:

1. **Retag and reload the image with a new tag:**
  ```bash
  docker build -t chaos-monkey-app:v2 -f ./app/Dockerfile ./app
  kind load docker-image chaos-monkey-app:v2 --name umesh-cluster
  ```
2. **Edit your deployment.yaml** to use the new image tag:
  ```yaml
  image: chaos-monkey-app:v2
  imagePullPolicy: IfNotPresent
  ```
3. **Delete the old deployment and pods:**
  ```bash
  kubectl delete deployment chaos-monkey-deployment
  kubectl delete pod -l app=chaos-monkey
  ```
4. **Re-apply the deployment:**
  ```bash
  kubectl apply -f ./k8s/deployment.yaml
  ```
5. **Watch the pods:**
  ```bash
  kubectl get pods -l app=chaos-monkey -w
  ```

This process forces Kubernetes to use the new image and clears any old references or cache issues. If you still encounter issues, double-check all image names, tags, and context, and seek help with your exact error messages and steps taken.

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
