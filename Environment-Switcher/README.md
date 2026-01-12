# Environment Switcher 🚀

A beginner-friendly Kubernetes project demonstrating how to use **Kustomize** to deploy the same application with different configurations for Development and Production environments from a single base YAML configuration.

## 🎯 Project Overview

This project showcases:
- **Kustomize overlays** for environment-specific configurations
- **Python Flask** web application displaying environment information
- **Kubernetes deployments** with different resource allocations
- **One codebase, multiple environments** deployment strategy

## 📋 What You'll Learn

- ✅ How Kustomize works with base and overlay configurations
- ✅ How to patch Kubernetes manifests without duplicating YAML
- ✅ Environment-specific resource management (CPU, memory, replicas)
- ✅ Kubernetes namespace isolation
- ✅ How to deploy the same app with different settings
- ✅ Docker containerization and Kubernetes deployment

## 🏗️ Project Structure

```
Environment-Switcher/
├── README.md                          # This file
├── PROCEDURE.md                       # Step-by-step testing guide
├── app/                              # Python Flask application
│   ├── app.py                        # Main application
│   ├── requirements.txt              # Python dependencies
│   └── Dockerfile                    # Container image definition
└── k8s/                              # Kubernetes configurations
    ├── base/                         # Base configuration (shared)
    │   ├── deployment.yaml           # Base deployment manifest
    │   ├── service.yaml              # Base service manifest
    │   └── kustomization.yaml        # Base kustomization config
    └── overlays/                     # Environment-specific overrides
        ├── dev/                      # Development environment
        │   └── kustomization.yaml    # Dev patches and settings
        └── prod/                     # Production environment
            └── kustomization.yaml    # Prod patches and settings
```

## 🔧 How It Works

### Kustomize Architecture

```
┌─────────────────────────────────────────┐
│          Base Configuration             │
│  (deployment.yaml + service.yaml)       │
│                                         │
│  • 1 replica                            │
│  • Basic resources (100m CPU, 128Mi)   │
│  • Generic environment variables        │
└─────────────────┬───────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
    ┌────▼─────┐    ┌─────▼────┐
    │   Dev    │    │   Prod   │
    │ Overlay  │    │  Overlay │
    └──────────┘    └──────────┘
```

### Environment Differences

| Feature          | Development       | Production        |
|------------------|-------------------|-------------------|
| **Namespace**    | `development`     | `production`      |
| **Name Prefix**  | `dev-`            | `prod-`           |
| **Replicas**     | 2                 | 3                 |
| **CPU Limit**    | 200m              | 500m              |
| **Memory Limit** | 256Mi             | 512Mi             |
| **Debug Mode**   | true              | false             |
| **API Version**  | v1.0.0            | v2.0.0            |
| **NodePort**     | 30002             | 30003             |
| **Color Theme**  | Blue/Teal         | Red               |

## 🚀 Quick Start

### Prerequisites

- Docker
- Kubernetes (Minikube, Kind, or Docker Desktop)
- kubectl
- kustomize (bundled with kubectl v1.14+)

### 1. Build the Docker Image

```bash
cd ~/Documents/Practise/Environment-Switcher
docker build -t env-switcher:latest ./app
```

### 2. Load Image into Cluster

**For Kind:**
```bash
kind load docker-image env-switcher:latest
```

**For Minikube:**
```bash
minikube image load env-switcher:latest
```

### 3. Create Namespaces

```bash
kubectl create namespace development
kubectl create namespace production
```

### 4. Deploy Development Environment

```bash
kubectl apply -k k8s/overlays/dev
```

### 5. Deploy Production Environment

```bash
kubectl apply -k k8s/overlays/prod
```

### 6. Access Applications

**For Docker Desktop:**
- **Development:** http://localhost:30002
- **Production:** http://localhost:30003

**For Kind (requires port-forwarding):**
```bash
# Development
kubectl port-forward -n development svc/dev-env-switcher 8080:80
# Access at: http://localhost:8080

# Production (in another terminal)
kubectl port-forward -n production svc/prod-env-switcher 8081:80
# Access at: http://localhost:8081
```

**For Minikube:**
```bash
minikube service dev-env-switcher -n development
minikube service prod-env-switcher -n production
```

## 📱 Application Features

The Flask web application displays:

- 🏷️ **Environment Badge** - Visual indicator of current environment
- 🖥️ **Hostname** - Pod identifier showing load balancing
- 📊 **Replicas** - Number of running instances
- ⚙️ **Resource Limits** - CPU and memory allocation
- 🔢 **API Version** - Version information
- 🐛 **Debug Mode** - Debug status
- ⏰ **Timestamp** - Current server time

## 🎨 Visual Differences

### Development Environment
- **Blue/Teal color scheme**
- Shows DEBUG_MODE: true
- Lower resource allocation
- Suitable for testing and development

### Production Environment
- **Red color scheme**
- Shows DEBUG_MODE: false
- Higher resource allocation
- Optimized for performance and reliability

## 🔍 Understanding Kustomize

### Base Configuration (`k8s/base/`)

The base contains the common configuration shared by all environments:
- Deployment with 1 replica
- Service exposing port 5000
- Basic resource limits
- Common labels

### Overlays (`k8s/overlays/`)

Each overlay applies **patches** to the base:

**Development Overlay:**
- Changes environment variables (ENVIRONMENT, REPLICAS, etc.)
- Increases replicas to 2
- Adjusts resources for dev workloads
- Changes NodePort to 30002
- Enables debug mode

**Production Overlay:**
- Changes environment to PRODUCTION
- Increases replicas to 3
- Allocates more resources (CPU/Memory)
- Changes NodePort to 30003
- Disables debug mode
- Updates API version

### Key Kustomize Features Used

1. **bases** - References the base configuration
2. **namePrefix** - Adds prefix to resource names (dev-, prod-)
3. **namespace** - Deploys to specific namespace
4. **commonLabels** - Adds labels to all resources
5. **replicas** - Overrides replica count
6. **patches** - JSON patches to modify specific fields

## 📚 Commands Reference

### Preview Generated Manifests

```bash
# View what will be deployed to dev
kubectl kustomize k8s/overlays/dev

# View what will be deployed to prod
kubectl kustomize k8s/overlays/prod

# Compare dev and prod
diff <(kubectl kustomize k8s/overlays/dev) <(kubectl kustomize k8s/overlays/prod)
```

### Deploy

```bash
# Deploy to dev
kubectl apply -k k8s/overlays/dev

# Deploy to prod
kubectl apply -k k8s/overlays/prod
```

### Monitor

```bash
# Watch dev pods
kubectl get pods -n development -w

# Watch prod pods
kubectl get pods -n production -w

# View dev logs
kubectl logs -n development -l app=env-switcher

# View prod logs
kubectl logs -n production -l app=env-switcher
```

### Scale

```bash
# Scale dev deployment
kubectl scale deployment dev-env-switcher -n development --replicas=4

# Scale prod deployment
kubectl scale deployment prod-env-switcher -n production --replicas=5
```

### Cleanup

```bash
# Delete dev environment
kubectl delete -k k8s/overlays/dev

# Delete prod environment
kubectl delete -k k8s/overlays/prod

# Delete namespaces
kubectl delete namespace development production
```

## 🧪 Testing

For detailed step-by-step testing instructions, see [PROCEDURE.md](PROCEDURE.md).

## 🛠️ Customization Ideas

Try these modifications to learn more:

1. **Add a Staging Environment**
   - Create `k8s/overlays/staging/`
   - Use 2 replicas with medium resources
   - Use orange color theme

2. **Add ConfigMap**
   - Store configuration in ConfigMap
   - Reference in deployment

3. **Add Secrets**
   - Store sensitive data
   - Use in environment variables

4. **Add Ingress**
   - Replace NodePort with Ingress
   - Add domain-based routing

5. **Modify Python App**
   - Add database connection info
   - Add more metrics
   - Add health check endpoint

## 📖 Additional Resources

- [Kustomize Documentation](https://kustomize.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Documentation](https://docs.docker.com/)

## 🤔 Troubleshooting

### Pods Won't Start

```bash
# Check pod status
kubectl describe pod <POD_NAME> -n <NAMESPACE>

# Check logs
kubectl logs <POD_NAME> -n <NAMESPACE>
```

### Image Not Found

Make sure you loaded the image:
```bash
# For Kind
kind load docker-image env-switcher:latest

# For Minikube
minikube image load env-switcher:latest
```

### Can't Access via Browser

**For Minikube:**
```bash
minikube service dev-env-switcher -n development
```

**For Kind:**
```bash
kubectl port-forward -n development svc/dev-env-switcher 8080:80
```

## 💡 Key Takeaways

1. **DRY Principle** - Kustomize eliminates YAML duplication
2. **Environment Parity** - Same base, different configurations
3. **Namespace Isolation** - Separate environments safely
4. **Resource Management** - Environment-specific resource allocation
5. **Patch System** - Surgical modifications without full rewrites
6. **GitOps Ready** - Easy to version control and manage

## 🎓 Learning Path

1. Start with [PROCEDURE.md](PROCEDURE.md) - Follow step-by-step
2. Deploy both environments
3. Compare the differences in browser
4. Study the kustomization.yaml files
5. Try modifying the patches
6. Create your own overlay (staging)
7. Experiment with different configurations

## 📝 License

This is an educational project. Feel free to use and modify for learning purposes.

## 🤝 Contributing

This is a learning project. Feel free to:
- Add more features
- Improve documentation
- Create additional overlays
- Enhance the Python application

---

**Happy Learning! 🚀**

*This project demonstrates production-ready Kubernetes patterns in a beginner-friendly way.*
