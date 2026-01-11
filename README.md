# Kubernetes Features — Demo Suite

Three focused Kubernetes labs that demonstrate core platform behaviors end-to-end: resilience when pods are killed, resource governance with requests/limits/quotas, and real Service-level load balancing across replicas. Each folder includes a runnable app, Kubernetes manifests, and a guided procedure so you can reproduce and observe the behaviors yourself.

## Projects

### 🔥 [Chaos-Monkey — Kubernetes Pod Deletion Example](Chaos-Monkey/README.md)
Induce random pod failures and watch Kubernetes self-heal in real-time. Deploy a Flask app, run a chaos script that deletes pods at random, and observe how Deployments replace them while Services maintain traffic flow. Perfect for understanding resilience and recovery patterns.

### 📊 [Resource-Limiter — Kubernetes Resource Limits & Quotas Demo](Resource-Limiter/README.md)
Explore resource governance through requests, limits, and quotas. Allocate memory on-demand to trigger throttling and OOM scenarios, inspect pod restarts, and learn how Kubernetes enforces resource boundaries at both pod and namespace levels.

### ⚖️ [Multi-Replica-Web-Server — Kubernetes Load Balancing Demo](Multi-Replica-Web-Server/README.md)
See Service-level load balancing in action across 5 replicas. Send traffic and identify which pod serves each request, understand traffic distribution patterns, and learn why port-forwarding differs from real in-cluster routing.

## Getting Around

- Start here for a quick map, then follow each project’s README and PROCEDURE for the walkthrough.
- Every project includes app code, Dockerfile, Kubernetes manifests, and a step-by-step runbook.
