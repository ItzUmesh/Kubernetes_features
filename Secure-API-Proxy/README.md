# Secure API Proxy (Kubernetes Secret Demo)

A minimal Python proxy that forwards requests to an upstream API. Access is protected by an API key stored in a Kubernetes Secret; the upstream URL comes from a ConfigMap. This is beginner-friendly: only the Python standard library and simple manifests.

## What you learn
- How to mount a Secret as environment variables and keep API keys out of code
- How to set an upstream URL via ConfigMap
- How to deploy a basic Python service with Deployment + Service
- How to test the API key check with curl

## Features
- Rejects requests without the correct `X-API-KEY` header (compares to Secret)
- Forwards GET/POST to an upstream URL with the same path
- Passes the API key upstream via `X-API-KEY` header (adjust as needed)
- Clear 401 responses when the key is missing or wrong

## Quick start (locally)
1. Set env vars and run:
   ```bash
   export API_KEY=dev-key
   export UPSTREAM_URL=https://httpbin.org
   python app/app.py
   ```
2. Test (should get 200):
   ```bash
   curl -i -H "X-API-KEY: dev-key" http://localhost:8080/get
   ```
3. Wrong key (should get 401):
   ```bash
   curl -i -H "X-API-KEY: wrong" http://localhost:8080/get
   ```

## Kubernetes deployment
- Create Secret (API key) and ConfigMap (upstream URL).
- Deploy Deployment and Service.
- Hit the Service with the right `X-API-KEY`.

See PROCEDURE.md for step-by-step apply/test commands.
