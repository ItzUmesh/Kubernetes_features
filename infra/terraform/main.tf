## Deploy the Helm chart using the Helm provider.
##
## This example references a local chart path (see variable `chart_path`).
resource "helm_release" "dynamic_time_portal" {
  name      = var.release_name
  chart     = var.chart_path
  namespace = var.namespace

  # Provide lightweight overrides for chart values. Here we only
  # set the image repository and tag; expand as needed.
  values = [
    yamlencode({
      image = {
        repository = "dynamic-time-portal"
        tag        = "latest"
      }
    })
  ]
}
