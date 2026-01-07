output "release_name" {
  value = helm_release.dynamic_time_portal.name
}

output "release_status" {
  value = helm_release.dynamic_time_portal.status
}
