# Chaos Monkey — Kubernetes Pod Deletion Example

This repository contains a tiny web app and a "Chaos Monkey" script that randomly
deletes pods so you can observe how Kubernetes (Deployment/ReplicaSet) recreates
them to maintain the declared replica count.

Repository layout
- `app/` — simple Flask application, `requirements.txt`, and `Dockerfile`.
- `k8s/` — `deployment.yaml` and `service.yaml` to run the app in Kubernetes.
- `chaos/` — `chaos-monkey.sh`: script that deletes pods matching a label selector.
- `PROCEDURE.md` — clear Run / Test / Observe / Stop steps for beginners.

Summary
1. Build the container image and make it available to your cluster (local or remote).
2. Deploy the Kubernetes manifests in `k8s/`.
3. Start the chaos script in `chaos/` to delete pods at an interval.
4. Observe Kubernetes recreating pods; stop the test when done.

Build and load image (examples)

From this project root you can build the image locally. Replace `chaos-monkey-app:latest`
with the tag you prefer.

```bash
# Build image using local Docker
docker build -t chaos-monkey-app:latest -f ./app/Dockerfile ./app

# For kind: load the image into the cluster
kind load docker-image chaos-monkey-app:latest

# For minikube: use the minikube docker daemon
eval $(minikube docker-env) && docker build -t chaos-monkey-app:latest ./app
```

Deploy to Kubernetes

```bash
kubectl apply -f ./k8s/deployment.yaml
kubectl apply -f ./k8s/service.yaml
kubectl get pods -l app=chaos-monkey
```

Run the chaos script

```bash
chmod +x ./chaos/chaos-monkey.sh
./chaos/chaos-monkey.sh --namespace default --label app=chaos-monkey --interval 5
```

Stop the test
- Press Ctrl-C to stop the running script.
- Optionally remove the deployment and service:

```bash
kubectl delete -f ./k8s/deployment.yaml
kubectl delete -f ./k8s/service.yaml
```

Notes & troubleshooting

- Deployment vs Service: A `Deployment` manages pod replicas and updates. A `Service`
	provides a stable network endpoint and load-balances traffic to pods with matching labels.
- `set -euo pipefail` is used in the chaos script: it makes the script fail-fast and
	helps catch bugs (see `chaos/chaos-monkey.sh` comments).
- If pods show `ErrImagePull` or `ImagePullBackOff`, see `PROCEDURE.md` for troubleshooting
	and common fixes (wrong image name, private registry, network/DNS issues).

See `PROCEDURE.md` for an explicit Run → Test → Observe → Stop procedure beginners can follow.
