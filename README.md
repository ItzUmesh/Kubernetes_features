# Kubernetes Features — Demo Suite

Three focused Kubernetes labs that demonstrate core platform behaviors end-to-end: resilience when pods are killed, resource governance with requests/limits/quotas, and real Service-level load balancing across replicas. Each folder includes a runnable app, Kubernetes manifests, and a guided procedure so you can reproduce and observe the behaviors yourself.

## Projects

- [Chaos-Monkey — Kubernetes Pod Deletion Example](Chaos-Monkey/README.md) — Delete pods at random and watch the Deployment replace them while the Service keeps traffic flowing.
- [Resource-Limiter — Kubernetes Resource Limits & Quotas Demo](Resource-Limiter/README.md) — Push requests/limits and quotas to trigger throttling or OOMs, then inspect how Kubernetes reports and recovers.
- [Multi-Replica-Web-Server — Kubernetes Load Balancing Demo](Multi-Replica-Web-Server/README.md) — Drive traffic through a Service to see 5 replicas share load and pinpoint which pod served each response.

## Getting Around

- Start here for a quick map, then follow each project’s README and PROCEDURE for the walkthrough.
- Every project includes app code, Dockerfile, Kubernetes manifests, and a step-by-step runbook.
