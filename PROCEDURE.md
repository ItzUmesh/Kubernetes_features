# Environment Switcher - Testing Procedure

This guide will walk you through testing the Environment Switcher project using Kustomize to deploy Dev and Prod environments.

## Prerequisites

Before starting, ensure you have the following installed:
- Docker
- Kubernetes cluster (Minikube, Kind, or Docker Desktop)
- kubectl
- kustomize (usually bundled with kubectl v1.14+)

## Step 1: Verify Prerequisites

Check that all required tools are installed:

```bash
# Check Docker
docker --version

# Check Kubernetes
kubectl version --client

# Check Kustomize
kubectl kustomize --help
```

## Step 2: Build the Docker Image

Navigate to the project directory and build the Docker image:

```bash
cd ~/Documents/Practise/Environment-Switcher

# Build the Docker image
docker build -t env-switcher:latest ./app

# Verify the image was created
docker images | grep env-switcher
```

**Expected Output:** You should see `env-switcher:latest` in the list.

## Step 3: Load Image into Kubernetes (if using Kind or Minikube)

### For Kind:
```bash
kind load docker-image env-switcher:latest
```

### For Minikube:
```bash
minikube image load env-switcher:latest
```

### For Docker Desktop:
Skip this step - images are automatically available.

## Step 4: Preview Kustomize Configurations

Before deploying, let's see what Kustomize will generate:

### View Base Configuration:
```bash
kubectl kustomize k8s/base
```

**What to observe:** Base configuration with 1 replica, minimal resources.

### View Dev Configuration:
```bash
kubectl kustomize k8s/overlays/dev
```

**What to observe:**
- Namespace: `development`
- Name prefix: `dev-`
- Replicas: 2
- Environment: DEVELOPMENT
- Debug: enabled
- NodePort: 30002

### View Prod Configuration:
```bash
kubectl kustomize k8s/overlays/prod
```

**What to observe:**
- Namespace: `production`
- Name prefix: `prod-`
- Replicas: 3
- Environment: PRODUCTION
- Higher resources (500m CPU, 512Mi RAM)
- NodePort: 30003

## Step 5: Create Namespaces

Create the required namespaces:

```bash
kubectl create namespace development
kubectl create namespace production
```

**Verify:**
```bash
kubectl get namespaces
```

## Step 6: Deploy Development Environment

Deploy the Dev environment using Kustomize:

```bash
kubectl apply -k k8s/overlays/dev
```

**Expected Output:**
```
deployment.apps/dev-env-switcher created
service/dev-env-switcher created
```

**Verify deployment:**
```bash
# Check pods in development namespace
kubectl get pods -n development

# Check service
kubectl get svc -n development

# Check deployment details
kubectl get deployment -n development -o wide
```

**Expected Results:**
- 2 pods running (as specified in dev overlay)
- Service exposed on NodePort 30002
- Labels showing environment: development

## Step 7: Test Development Environment

Access the Dev application:

**For Docker Desktop:**
- URL: `http://localhost:30002`

**For Kind (requires port-forwarding):**
```bash
# Set up port forwarding
kubectl port-forward -n development svc/dev-env-switcher 8080:80
```
- URL: `http://localhost:8080`
- Keep the terminal running while accessing the app

**For Minikube:**
```bash
# Use minikube service command
minikube service dev-env-switcher -n development
```

**Expected Display:**
- Badge color: Blue/Teal
- Environment: DEVELOPMENT
- Replicas: 2
- CPU Limit: 200m
- Memory Limit: 256Mi
- Debug Mode: true
- API Version: v1.0.0

## Step 8: Deploy Production Environment

Deploy the Prod environment:

```bash
kubectl apply -k k8s/overlays/prod
```

**Expected Output:**
```
deployment.apps/prod-env-switcher created
service/prod-env-switcher created
```

**Verify deployment:**
```bash
# Check pods in production namespace
kubectl get pods -n production

# Check service
kubectl get svc -n production

# Check deployment details
kubectl get deployment -n production -o wide
```

**Expected Results:**
- 3 pods running (as specified in prod overlay)
- Service exposed on NodePort 30003
- Labels showing environment: production

## Step 9: Test Production Environment

Access the Prod application:

**For Docker Desktop:**
- URL: `http://localhost:30003`

**For Kind (in a new terminal):**
```bash
# Set up port forwarding
kubectl port-forward -n production svc/prod-env-switcher 8081:80
```
- URL: `http://localhost:8081`

**For Minikube:**
```bash
minikube service prod-env-switcher -n production
```

**Expected Display:**
- Badge color: Red
- Environment: PRODUCTION
- Replicas: 3
- CPU Limit: 500m
- Memory Limit: 512Mi
- Debug Mode: false
- API Version: v2.0.0

## Step 10: Compare Configurations Side-by-Side

Open both environments in separate browser tabs and compare:

**For Docker Desktop:**
- Dev: `http://localhost:30002`
- Prod: `http://localhost:30003`

**For Kind:**
- Dev: `http://localhost:8080` (with port-forward running)
- Prod: `http://localhost:8081` (with port-forward running)

**Key Differences to Observe:**
1. **Color Scheme:** Dev (blue/teal) vs Prod (red)
2. **Replicas:** Dev (2) vs Prod (3)
3. **Resources:** Dev (200m/256Mi) vs Prod (500m/512Mi)
4. **Debug Mode:** Dev (true) vs Prod (false)
5. **API Version:** Dev (v1.0.0) vs Prod (v2.0.0)
6. **Hostname:** Different pod names due to name prefix

## Step 11: Verify Kustomize Differences

Use diff to compare the generated manifests:

```bash
diff <(kubectl kustomize k8s/overlays/dev) <(kubectl kustomize k8s/overlays/prod)
```

**What to observe:** All the patches applied by Kustomize to transform base into dev/prod.

## Step 12: Scale and Update

Test updating an environment:

```bash
# Scale dev to 3 replicas
kubectl scale deployment dev-env-switcher -n development --replicas=3

# Watch the scaling
kubectl get pods -n development -w
```

**Refresh the browser** - you should see different hostnames as you refresh (load balancing).

## Step 13: Check Resource Usage

Compare resource allocation:

```bash
# Dev resources
kubectl describe deployment dev-env-switcher -n development | grep -A 5 "Limits:"

# Prod resources
kubectl describe deployment prod-env-switcher -n production | grep -A 5 "Limits:"
```

## Step 14: View Logs

Check application logs:

```bash
# Dev logs
kubectl logs -n development -l app=env-switcher --tail=20

# Prod logs
kubectl logs -n production -l app=env-switcher --tail=20
```

## Step 15: Cleanup

Remove all deployed resources:

```bash
# Delete dev environment
kubectl delete -k k8s/overlays/dev

# Delete prod environment
kubectl delete -k k8s/overlays/prod

# Delete namespaces (optional)
kubectl delete namespace development
kubectl delete namespace production
```

**Verify cleanup:**
```bash
kubectl get pods --all-namespaces | grep env-switcher
```

Should return nothing.

## Troubleshooting

### Pods not starting:
```bash
kubectl describe pod <POD_NAME> -n <NAMESPACE>
kubectl logs <POD_NAME> -n <NAMESPACE>
```

### Image pull errors:
- Make sure you loaded the image into your cluster (Step 3)
- Check image name matches exactly: `env-switcher:latest`

### Cannot access via NodePort:
- For Minikube: Use `minikube service <SERVICE_NAME> -n <NAMESPACE>`
- For Kind: May need port forwarding: `kubectl port-forward -n <NAMESPACE> svc/<SERVICE_NAME> 8080:80`

### Kustomize not found:
```bash
# Install kustomize separately if needed
kubectl version --client
# or
brew install kustomize  # macOS
```

## Learning Outcomes

After completing this procedure, you should understand:

1. ✅ How Kustomize uses a base configuration with overlays
2. ✅ How to apply patches to modify Kubernetes resources
3. ✅ The difference between dev and prod configurations
4. ✅ How to deploy the same app to different environments
5. ✅ How to use `kubectl apply -k` to apply Kustomize configs
6. ✅ How namespaces isolate environments
7. ✅ How namePrefix prevents resource conflicts
8. ✅ How to configure environment-specific resources and replicas

## Next Steps

Try modifying the configurations:
- Add a staging environment in `k8s/overlays/staging`
- Change resource limits in the overlays
- Add ConfigMaps or Secrets
- Modify the Python app to show more environment info
