## Terraform provider configuration
##
## This file configures the Terraform providers used to talk to
## Kubernetes and the Helm provider. It expects a kubeconfig file
## path supplied via `var.kubeconfig_path`.

terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = ">= 2.0.0"
    }
  }
}

# Use the local kubeconfig file by default. You can override the
# `kubeconfig_path` variable when running `terraform` if needed.
provider "kubernetes" {
  config_path = var.kubeconfig_path
}

# The Helm provider needs access to the same Kubernetes cluster.
provider "helm" {
  kubernetes {
    config_path = var.kubeconfig_path
  }
}
