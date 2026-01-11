# Kubernetes Features — Demo Suite

Three focused Kubernetes labs to explore core platform behaviors: resilience under pod failure, resource governance with requests/limits/quotas, and real Service-level load balancing. Each folder includes a runnable app, manifests, and a guided procedure so you can reproduce the scenarios yourself.

## Projects

- [Chaos-Monkey/README.md](Chaos-Monkey/README.md) — Trigger random pod deletions and watch Deployments and Services keep the app reachable.
- [Resource-Limiter/README.md](Resource-Limiter/README.md) — Push requests/limits and quotas to see scheduling, throttling, and OOM restarts in a controlled lab.
- [Multi-Replica-Web-Server/README.md](Multi-Replica-Web-Server/README.md) — Send traffic through a Service to observe 5 replicas sharing load and identify which pod handled each call.

## Getting Around

- Start here for a quick map, then follow each project’s README and PROCEDURE for the walkthrough.
- Every project includes app code, Dockerfile, Kubernetes manifests, and a step-by-step runbook.
