# PROCEDURE — Run / Test / Observe / Stop

This procedure walks a beginner through running the app, exercising the chaos script,
observing Kubernetes behavior, and stopping/cleaning up.

Prerequisites
- `kubectl` configured to point at your cluster (or minikube/kind). Use `kubectl cluster-info`.
- `docker`, `kind`, or `minikube` available locally if you plan to build and load images.

1) Run — build image and deploy

- Build the image locally:

```bash
docker build -t chaos-monkey-app:latest -f ./app/Dockerfile ./app
```

- Load the image into your local cluster if needed:

For kind:
```bash
kind load docker-image chaos-monkey-app:latest
```

For minikube:
```bash
eval $(minikube docker-env)
docker build -t chaos-monkey-app:latest ./app
```

- Deploy the app to Kubernetes:

```bash
kubectl apply -f ./k8s/deployment.yaml
kubectl apply -f ./k8s/service.yaml
kubectl get pods -l app=chaos-monkey
```

2) Test — confirm the app is serving

- Check pods and logs:

```bash
kubectl get pods -l app=chaos-monkey
kubectl logs -l app=chaos-monkey --tail=50
```

- If you have a ClusterIP service, port-forward to test locally:

```bash
kubectl port-forward svc/chaos-monkey-service 8080:80
# In another terminal:
curl http://127.0.0.1:8080/
```

3) Observe test case — run the chaos script and watch behavior

- Start the chaos script (will loop until stopped):

```bash
chmod +x ./chaos/chaos-monkey.sh
./chaos/chaos-monkey.sh --namespace default --label app=chaos-monkey --interval 5
```

- In another terminal watch pods get deleted and recreated:

```bash
kubectl get pods -l app=chaos-monkey -w
```

- To inspect an event or reason for restarts or image pull failures use:

```bash
kubectl describe pod <pod-name> -n default
kubectl get events -n default --sort-by=.metadata.creationTimestamp
```

4) Stop — end the chaos run and clean up

- Stop the chaos script with Ctrl-C in the terminal running it.
- Confirm pods return to the desired replica count:

```bash
kubectl get pods -l app=chaos-monkey
```

- Optional cleanup (remove app from cluster):

```bash
kubectl delete -f ./k8s/deployment.yaml
kubectl delete -f ./k8s/service.yaml
```

Troubleshooting common problems

- Image pull errors (`ErrImagePull`, `ImagePullBackOff`):
  - Confirm the image name and tag in `k8s/deployment.yaml` match a pushed or loaded image.
  - For private registries, create an `imagePullSecret` and reference it in the pod spec.
  - Inspect `kubectl describe pod <pod>` for the exact error message (e.g., `manifest unknown`, `unauthorized`).

- Script errors or missing `kubectl`: ensure `kubectl` is on PATH and your kubeconfig points to the intended cluster.

- If pods are stuck terminating or not recreating: check the Deployment's `replicas` value and `kubectl describe deployment` for errors.

If you want, I can: (a) run these steps against a local kind/minikube cluster, or (b) help you add an `imagePullSecret` to the deployment. Which would you like? 
