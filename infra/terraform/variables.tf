## Variables used by Terraform to locate kubeconfig, chart and set
## the release/namespace parameters. Override via `-var` on the
## command line or create a `terraform.tfvars` file.

variable "kubeconfig_path" {
  description = "Path to kubeconfig file used by providers"
  type        = string
  default     = "~/.kube/config"
}

variable "release_name" {
  description = "Helm release name"
  type        = string
  default     = "dynamic-time-portal"
}

variable "chart_path" {
  description = "Path to the local Helm chart"
  type        = string
  default     = "../helm/dynamic-time-portal"
}

variable "namespace" {
  description = "Kubernetes namespace to deploy into"
  type        = string
  default     = "default"
}
