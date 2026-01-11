# PROCEDURE: Secure API Proxy

Step-by-step to deploy a Python proxy that uses a Kubernetes Secret for an API key and a ConfigMap for the upstream URL.

## Prereqs
- Kubernetes cluster and `kubectl` configured
- Namespace: `secure-api-proxy`

## 1) Create Secret and ConfigMap
```bash
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
```

## 2) Deploy app and service
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## 3) Verify pods
```bash
kubectl get pods -n secure-api-proxy
kubectl logs deploy/secure-api-proxy -n secure-api-proxy
```

## 4) Test (replace NODE_PORT or use port-forward)
```bash
# Option A: port-forward
kubectl port-forward deploy/secure-api-proxy 8080:8080 -n secure-api-proxy &

# Option B: if using NodePort or LoadBalancer, set SERVICE_HOST:PORT accordingly
```

## 5) Make requests
```bash
# Should succeed
curl -i -H "X-API-KEY: demo-secret-key" http://localhost:8080/get

# Should fail (401)
curl -i -H "X-API-KEY: wrong" http://localhost:8080/get
```

## 6) Clean up
```bash
kubectl delete namespace secure-api-proxy
```
