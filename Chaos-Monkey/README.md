# Chaos Monkey - Kubernetes Pod Deletion Example

This small project demonstrates a simple app deployed to Kubernetes and a "Chaos Monkey" script
that randomly deletes pods so you can watch Kubernetes recreate them.

Contents
- `app/` - simple Flask app, Dockerfile, and requirements
- `k8s/` - Kubernetes manifests for Deployment and Service
- `chaos/` - chaos script that randomly deletes pods

Quick overview
1. Build the app image and load/push it to your cluster (instructions below).
2. Deploy the Kubernetes manifests: `kubectl apply -f k8s/`.
3. Run the chaos script: `./chaos/chaos-monkey.sh` to randomly delete pods.
4. Stop the script with Ctrl-C and observe pods being recreated automatically.

Supported local workflows
- Minikube: use `minikube image build -t <image>` or `eval $(minikube docker-env)` then `docker build`.
- Kind: use `docker build -t <image>` then `kind load docker-image <image>`.

Example commands (replace image name as shown below):

Build image locally (example):

```bash
# From the workspace root
docker build -t chaos-monkey-app:latest -f "/home/testuser/Documents/Practise/Chaos-Monkey/app/Dockerfile" "/home/testuser/Documents/Practise/Chaos-Monkey/app"

# For kind: kind load docker-image chaos-monkey-app:latest
# For minikube: eval $(minikube docker-env) && docker build -t chaos-monkey-app:latest "/home/testuser/Documents/Practise/Chaos-Monkey/app"
```

Deploy to Kubernetes:

```bash
kubectl apply -f "/home/testuser/Documents/Practise/Chaos-Monkey/k8s/deployment.yaml"
kubectl apply -f "/home/testuser/Documents/Practise/Chaos-Monkey/k8s/service.yaml"
kubectl get pods -l app=chaos-monkey
```

Run the chaos script (will run until you press Ctrl-C):

```bash
chmod +x "/home/testuser/Documents/Practise/Chaos-Monkey/chaos/chaos-monkey.sh"
cd "/home/testuser/Documents/Practise/Chaos-Monkey/chaos"
./chaos-monkey.sh --namespace default --label app=chaos-monkey --interval 5
```

Stopping the test
- Press Ctrl-C in the terminal running the chaos script to stop deleting pods.
- Optionally remove the deployment: `kubectl delete -f "/home/testuser/Documents/Practise/Chaos-Monkey/k8s/deployment.yaml"`.

Notes for beginners
- Deleting a pod does not delete the Deployment. The Deployment controller immediately notices and creates a replacement pod to maintain the desired replica count.
- The script simply automates pod deletion so you can observe this behavior.
