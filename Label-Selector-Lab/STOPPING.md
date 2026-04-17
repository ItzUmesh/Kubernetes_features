# Stopping Label-Selector-Lab

Use these steps to stop the project safely.

## 1) Stop running terminal commands
If `selector.py` or `kubectl port-forward` is running, press:

```bash
Ctrl + C
```

## 2) Delete lab resources from Kubernetes

```bash
kubectl delete namespace label-selector-lab
```

## 3) Verify it is stopped

```bash
kubectl get ns label-selector-lab
```

If you see `NotFound`, the lab is fully stopped.

---

## Optional full cleanup

Remove local Docker image:

```bash
docker rmi label-selector-app:latest
```

Delete the kind cluster (stops everything in that cluster):

```bash
kind delete cluster
```
