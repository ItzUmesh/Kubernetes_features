# Notes — Chaos Monkey project

## Deployment vs Service

- **Deployment**: declares how to run pods. It manages replica count, rolling updates, and restarts. Key fields: `spec.replicas`, `spec.template` (pod spec), and `selector`.
- **Service**: exposes a stable network endpoint (IP/DNS) and load-balances traffic to pods matching its `spec.selector`. Key fields: `spec.selector`, `spec.ports`, `spec.type`.

How they work together:
- Create a `Deployment` to run pods with a label (e.g., `app=chaos-monkey`).
- Create a `Service` that selects that label so clients can reliably reach the pods even when pods are recreated.

Useful commands:

```
kubectl get deployments
kubectl get pods -l app=chaos-monkey
kubectl get svc
kubectl describe deployment chaos-monkey-deployment
kubectl describe svc chaos-monkey-service
```

## Note about `image: chaos-monkey-app:latest`

- The `deployment.yaml` uses `image: chaos-monkey-app:latest`. Replace that with the image tag you build and load/push into your cluster (for `kind` load the docker-image, for `minikube` use the minikube docker env or push to a registry).

## `set -euo pipefail` (bash safety flags)

- `set -e` (errexit): exit immediately if a command exits with a non-zero status.
- `set -u` (nounset): treat unset variables as an error and exit.
- `set -o pipefail`: a pipeline fails if any command in it fails (not just the last).

Quick example:

```
# Without pipefail this pipeline returns status 0 (last command succeeds)
false | true

# With pipefail the pipeline returns non-zero if any command fails
set -o pipefail
false | true
```

In `chaos/chaos-monkey.sh` these flags make the script fail-fast and more robust. Use `|| true` or temporarily `set +e` if you expect a command to fail and want to continue.
