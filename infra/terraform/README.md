# Terraform infra for Dynamic Time Portal

This small Terraform module demonstrates using the Helm provider to
install the local Helm chart into a Kubernetes cluster.

Usage:

1. Ensure you have `kubectl` configured and `KUBECONFIG` or a kubeconfig at the path in `var.kubeconfig_path`.
2. From this folder run:

```bash
terraform init
terraform apply -var="kubeconfig_path=$HOME/.kube/config"
```

Notes:
- The configuration assumes a local Helm chart at `../helm/dynamic-time-portal`.
- Adjust provider settings in `providers.tf` if you use other auth methods.

This is intended as an example for beginners; adapt and secure credentials
appropriately before using in production.
