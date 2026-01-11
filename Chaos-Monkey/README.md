
# Chaos Monkey — Kubernetes Pod Deletion Example

## Overview
This project demonstrates Kubernetes self-healing by running a simple web app in a Deployment and using a "Chaos Monkey" script to randomly delete pods. Kubernetes will automatically recreate deleted pods, letting you observe its resilience in action.

## Features
- Minimal Flask web app that returns its pod hostname (see `app/`).
- Dockerfile and requirements for easy containerization.
- Kubernetes manifests for Deployment (with liveness/readiness probes) and Service (see `k8s/`).
- Bash chaos script (`chaos/chaos-monkey.sh`) that randomly deletes pods by label.
- Step-by-step manual procedure in `PROCEDURE.md` for building, deploying, testing, observing, and troubleshooting.

## Project Structure
- `app/` — Flask app, Dockerfile, requirements.txt
- `k8s/` — Kubernetes manifests: deployment.yaml, service.yaml
- `chaos/` — chaos-monkey.sh script
- `PROCEDURE.md` — full manual procedure and troubleshooting

## Quick Start (Summary)
1. Build the Docker image:
	```bash
	docker build -t chaos-monkey-app:latest -f ./app/Dockerfile ./app
	```
2. Load the image into your cluster (see PROCEDURE.md for kind/minikube/remote):
	```bash
	kind load docker-image chaos-monkey-app:latest
	# or for minikube:
	eval $(minikube docker-env)
	docker build -t chaos-monkey-app:latest ./app
	```
3. Deploy to Kubernetes:
	```bash
	kubectl apply -f ./k8s/deployment.yaml
	kubectl apply -f ./k8s/service.yaml
	kubectl get pods -l app=chaos-monkey
	```
4. Run the chaos script:
	```bash
	chmod +x ./chaos/chaos-monkey.sh
	./chaos/chaos-monkey.sh --namespace default --label app=chaos-monkey --interval 5
	```
5. Observe pods being deleted and recreated. Stop the script with Ctrl-C.
6. For full details, troubleshooting, and manual checks, see `PROCEDURE.md`.

## Troubleshooting
- If pods are stuck in `ImagePullBackOff` or `ErrImagePull`, see the troubleshooting section in `PROCEDURE.md` for step-by-step fixes (image not loaded, private registry, wrong tag, etc).
- For networking or DNS issues, see manual checks in `PROCEDURE.md`.

## How it works
- The Deployment ensures a fixed number of pods are always running.
- The Service provides a stable endpoint to access the app.
- The chaos script deletes pods at random intervals; the Deployment controller immediately creates replacements.

## See Also
- Full manual procedure and troubleshooting: [PROCEDURE.md](PROCEDURE.md)
- Chaos script with comments: [chaos/chaos-monkey.sh](chaos/chaos-monkey.sh)

