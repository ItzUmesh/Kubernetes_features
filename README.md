# Kubernetes Features — Demo Suite

Three focused Kubernetes labs you can run end-to-end: watch self-healing under pod failure, see how limits and quotas change pod behavior, and observe real load balancing across replicas. Each folder ships with a runnable app, manifests, and a guided procedure.

## Projects

- [Chaos-Monkey/README.md](Chaos-Monkey/README.md) — Induce random pod deletions and see Deployments self-heal without breaking the service.
- [Resource-Limiter/README.md](Resource-Limiter/README.md) — Stress requests/limits and quotas to trigger throttling and OOM restarts, then inspect what Kubernetes reports.
- [Multi-Replica-Web-Server/README.md](Multi-Replica-Web-Server/README.md) — Drive traffic through a Service to watch 5 replicas share load and confirm which pod served each request.

## Getting Around

- Start here for a quick map, then follow each project’s README and PROCEDURE for the walkthrough.
- Every project includes app code, Dockerfile, Kubernetes manifests, and a step-by-step runbook.
