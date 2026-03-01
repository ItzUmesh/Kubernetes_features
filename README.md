<p align="center">
  <img src="https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white" alt="Kubernetes"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Helm-0F1689?style=for-the-badge&logo=helm&logoColor=white" alt="Helm"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
</p>

<h1 align="center">☸️ The Ultimate Kubernetes Feature-Lab</h1>
<h3 align="center"><span style="color:#326CE5">37+ Projects</span> — Deep-diving into the K8s API through Python-driven automation and infrastructure-as-code</h3>

---

## <span style="color:#22c55e">🟢 Phase A: Core Fundamentals</span> <span style="color:#94a3b8">(The Basics)</span>

| # | Project | Description |
|---|---------|-------------|
| 1 | 🔄 **Multi-Replica-Web-Server** | Test load balancing and pod replication. |
| 2 | 💓 **Health-Check-Demo** | Use Python to create endpoints that fail, testing Liveness and Readiness probes. |
| 3 | 📊 **Resource-Limiter** | Test CPU/Memory quotas and see how K8s handles OOMKilled events. |
| 4 | 🏷️ **Label-Selector-Lab** | Use a Python script to filter and list pods based on custom labels. |

---

## <span style="color:#eab308">🟡 Phase B: Configuration & Secrets</span>

| # | Project | Description |
|---|---------|-------------|
| 5 | 🎨 **Dynamic-Theme-App** | Use ConfigMaps to change app behavior without a restart. |
| 6 | 🔐 **Secure-API-Proxy** | Manage sensitive API keys using Kubernetes Secrets. |
| 7 | 🔀 **Environment-Switcher** | Use Kustomize to manage Dev vs. Prod environments. |
| 8 | 👁️ **Config-Hot-Reloader** | Write a Python "watcher" that detects when a ConfigMap changes and restarts the app logic. |

---

## <span style="color:#3b82f6">🔵 Phase C: Resilience & Scheduling</span>

| # | Project | Description |
|---|---------|-------------|
| 9 | 🐵 **Chaos-Monkey** | Use the Python K8s client to randomly delete pods and watch them self-heal. |
| 10 | 🎯 **Node-Affinity-Router** | Force pods onto specific nodes (e.g., "high-memory" or "gpu" labels). |
| 11 | 🚫 **Taint-and-Toleration-Test** | Secure a node so only specific "authorized" pods can land there. |
| 12 | 🌍 **Topology-Spreader** | Ensure replicas are spread across different availability zones (AZs). |

---

## <span style="color:#f97316">🟠 Phase D: Storage & State</span>

| # | Project | Description |
|---|---------|-------------|
| 13 | 💾 **Persistent-Guestbook** | Test PersistentVolumes (PV) and Claims (PVC) with a database like Postgres. |
| 14 | 💬 **Stateful-Messenger** | Deploy a StatefulSet to give each pod a unique, persistent identity. |
| 15 | 📸 **Storage-Snapshot-Manager** | Use Python to automate taking snapshots of your persistent disks. |

---

## <span style="color:#ef4444">🔴 Phase E: Networking & Security</span>

| # | Project | Description |
|---|---------|-------------|
| 16 | 🌐 **Ingress-Controller-Setup** | Route traffic to multiple Python services via subdomains using Nginx Ingress. |
| 17 | 🛡️ **Network-Firewall-Demo** | Use NetworkPolicies to block all traffic except for a specific whitelist. |
| 18 | 🔑 **RBAC-Role-Player** | Create restricted ServiceAccounts for your Python scripts to limit their API access. |
| 19 | 🚦 **Gateway-API-Lab** | Test the modern replacement for Ingress to handle advanced traffic splitting. |

---

## <span style="color:#a855f7">🟣 Phase F: Scaling & Automation</span> <span style="color:#94a3b8">(Senior Level)</span>

| # | Project | Description |
|---|---------|-------------|
| 20 | 📈 **HPA-Stress-Tester** | Write a Python "load generator" to trigger Horizontal Pod Autoscaling. |
| 21 | 📐 **VPA-Right-Sizer** | Use the Vertical Pod Autoscaler to automatically adjust pod CPU/RAM limits. |
| 22 | ⏰ **CronJob-Cleaner** | Create a CronJob that runs a Python script to clean up old images or temp logs. |
| 23 | ✅ **Init-Container-Validator** | Use an Init-Container to check if a DB is ready before the main app starts. |

---

## <span style="color:#06b6d4">💎 Phase G: Extensibility</span> <span style="color:#94a3b8">(Platform Engineer Level)</span>

| # | Project | Description |
|---|---------|-------------|
| 24 | 🧩 **Custom-Resource (CRD) Demo** | Define your own object type in the K8s API (e.g., a "DatabaseBackup" object). |
| 25 | ⚙️ **Python-Operator-Lab** | Write a real Kubernetes Operator (using kopf) that automates a task when a CRD is created. |
| 26 | 🔒 **Admission-Webhook** | Write a Python service that "validates" deployments and rejects them if they don't have proper tags. |
| 27 | 📉 **Metric-Exporter** | Write a Python script to export custom application metrics to Prometheus. |

---

## <span style="color:#6366f1">🌐 Phase H: Platform Engineering & Developer Experience</span>

*These projects are about building "The Platform" that other developers use.*

| # | Project | Description |
|---|---------|-------------|
| 28 | 🖥️ **Internal Developer Portal (IDP)** | Build a small Python/Flask UI where a developer can click a button to provision a pre-configured K8s Namespace with all the right labels and network policies. |
| 29 | 🗄️ **Self-Service Database Provisioner** | Write a Python script that uses a Crossplane or Terraform Controller to spin up a managed database on OCI (Oracle Cloud) just by creating a YAML file in K8s. |
| 30 | 📚 **Golden-Path Template Library** | Create a Helm "Library Chart" that enforces corporate standards (like mandatory logging and specific security contexts) for every app in the company. |

---

## <span style="color:#ec4899">🤖 Phase I: AIOps & Advanced Automation</span>

*Perfect for leveraging your OCI AI Foundations certification.*

| # | Project | Description |
|---|---------|-------------|
| 31 | 🤖 **LLM-Based Log Analyzer** | Write a Python sidecar that sends "CrashLoopBackOff" logs to an LLM (via OCI Generative AI) to provide a human-readable summary of the fix. |
| 32 | 💰 **Automated Cost Optimizer** | Build a script that scans for underutilized pods (using metrics from Prometheus) and automatically suggests (or applies) lower Resource Limits. |
| 33 | ⚡ **Event-Driven Scaler (KEDA)** | Deploy KEDA to scale your Python app based on the number of messages in a queue (like Redis or RabbitMQ) instead of just CPU usage. |

---

## <span style="color:#dc2626">🛡️ Phase J: Governance & Security (DevSecOps)</span>

*Crucial for high-level DevOps interviews.*

| # | Project | Description |
|---|---------|-------------|
| 34 | 📋 **Policy-as-Code Guardrails** | Use Kyverno or OPA Gatekeeper to write a policy that says: "Any pod deployed without an 'Owner' label will be automatically rejected." |
| 35 | 🔍 **Software Bill of Materials (SBOM) Scanner** | Build a pipeline that scans every container image for vulnerabilities before it's allowed to run in the "Prod" namespace. |
| 36 | 🔗 **Multi-Cluster Federation** | Use Karmada or Cluster API to manage three different "sub-clusters" from one single "Management Cluster." |
| 37 | 🔬 **eBPF Observability Lab** | Use Cilium or Hubble to visualize exactly how your Python app is talking to other services at the Linux kernel level. |

---

<p align="center">
  <strong>📊 Total: 37+ hands-on projects across 10 phases</strong>
</p>
