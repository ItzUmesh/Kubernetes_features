# PROCEDURE: Secure API Proxy

Step-by-step to deploy a Python proxy that uses a Kubernetes Secret for an API key and a ConfigMap for the upstream URL.

## Prereqs
- Kubernetes cluster and `kubectl` configured
- Namespace: `secure-api-proxy`

## 1) Build the image
```bash
cd app
docker build -t docker.io/itzumesh/secure-api-proxy:v1 .
# Push if your cluster pulls from a registry
docker push docker.io/itzumesh/secure-api-proxy:v1
```
> Note: repository names must be lowercase. Keep the trailing `.` to set the build context.

### If using kind (no push needed)
```bash
kind load docker-image docker.io/itzumesh/secure-api-proxy:v1
```

### If using minikube (no push needed)
```bash
eval $(minikube docker-env)
docker build -t docker.io/itzumesh/secure-api-proxy:v1 .
```

## 2) Update Deployment with your image
Edit `k8s/deployment.yaml` and replace line 17 (`image: secure-api-proxy:latest`) with:
```yaml
image: docker.io/itzumesh/secure-api-proxy:v1
```
This ensures the Deployment pulls the correct image when applied.

## 3) Create Secret and ConfigMap
```bash
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
```

## 4) Deploy app and service
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## 5) Verify pods
```bash
kubectl get pods -n secure-api-proxy
kubectl logs deploy/secure-api-proxy -n secure-api-proxy
```

## 6) Test (replace NODE_PORT or use port-forward)
```bash
# Option A: port-forward
kubectl port-forward deploy/secure-api-proxy 8080:8080 -n secure-api-proxy &

# Option B: if using NodePort or LoadBalancer, set SERVICE_HOST:PORT accordingly
```

## 7) Make requests
```bash
# Should succeed
curl -i -H "X-API-KEY: demo-secret-key" http://localhost:8080/get

# Should fail (401)
curl -i -H "X-API-KEY: wrong" http://localhost:8080/get
```

## 8) Clean up
```bash
kubectl delete namespace secure-api-proxy
```
