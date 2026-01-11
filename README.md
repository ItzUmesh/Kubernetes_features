Author: Umesh NS
E-mail: umesh.DBA@hotmail.com

This repository features a series of Kubernetes hands-on projects designed to master cloud-native fundamentals. Each project was developed using VS Code and GitHub Copilot, following a curriculum suggested by Google Gemini to explore core K8s features incrementally.

1. The "Self-Healing" Basics
These projects teach you how Kubernetes maintains the Desired State.

1. Chaos Monkey Script: Build a simple app and write a script that randomly deletes pods to watch K8s recreate them.

2. Resource Limiter: Deploy a memory-intensive app and set ResourceQuotas to see how K8s throttles or kills "greedy" containers.

3. Multi-Replica Web Server: Deploy a site with 5 replicas and use kubectl logs -f to see how traffic is distributed.

4. Health Check Demo: Create an app with a /health endpoint that you can manually toggle to "fail," triggering a K8s restart.

2. Configuration & Secrets
Learn how to keep code and configuration separate.

5. Dynamic Theme App: A web app that changes its background color based on a ConfigMap.

6. Secure API Proxy: A small app that fetches data from a private API using an API key stored in a Kubernetes Secret.
-------------------------------------------------------To Be Continued. ------------------------------------------------------------------------
7. Environment Switcher: Use one YAML file to deploy "Dev" or "Prod" versions using Kustomize.

3. State & Storage (The Hard Part)
Containers are ephemeral; these projects teach you how to save data.

8. Persistent Guestbook: A simple CRUD app using PersistentVolumeClaims (PVC) so data survives a pod crash.

9. SQLite Shared Drive: Two different pods reading/writing to the same shared volume.

10. Database Deployment: Deploy a standalone PostgreSQL or MongoDB instance inside your cluster.

4. Networking & Routing
Learn how traffic moves in and out of the cluster.

11. Ingress Controller Setup: Use Nginx Ingress to route app.local/blog to one service and app.local/api to another.

12. Simple Load Balancer: Use a LoadBalancer service type to expose a hello-world app to your local network.

13. Internal "Private" Microservice: Create two apps where App A can talk to App B, but App B is not accessible from the internet.

5. Automation & Observability
Learn how to monitor and update your apps.

14. Zero-Downtime Deployment: Perform a "Rolling Update" from Version 1 to Version 2 of a website while running a load test.

15. Blue/Green Deployment: Manually switch a Service selector from one deployment (Blue) to another (Green).

16. Prometheus Dashboard: Deploy Prometheus and Grafana to see a live graph of your CPU usage.

17. Log Aggregator: Set up a basic Loki or ELK stack to search through logs from all your pods in one place.

6. Advanced Beginner (Jobs & Cron)
18. Nightly Database Backup: A CronJob that runs every night at 2 AM to "back up" a folder.

19. One-Time Image Processor: A Job that starts, resizes an image, and then shuts down completely.

20. The "Self-Destructing" App: An app that runs for 60 seconds, completes a task, and exits, teaching you how K8s handles "Completed" vs "Crashed" states.
