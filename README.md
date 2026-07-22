# Production-Grade Observability Stack (Prometheus + Grafana + Loki)

This repository implements a production-leaning observability stack on Kubernetes using Prometheus, Grafana, Loki, and Alertmanager integrated with a sample Flask application. 

## Architecture Overview

- Prometheus (kube-prometheus-stack) collects cluster and application metrics. 
- Loki + promtail aggregate structured JSON logs from Kubernetes pods. 
- Grafana visualizes metrics and logs and manages alerts. 
- Flask sample app exposes `/hello` and `/metrics` with Prometheus instrumentation and JSON logs. 

## Prerequisites

- Kubernetes cluster (Minikube, Kind, or managed K8s).
- Helm v3, kubectl, Docker.
- Access to a container registry.

## Setup Steps

1. Create namespace:

   ```bash
   kubectl create namespace observability-demo
   ```

2. Build and push the app image:

   ```bash
   cd app
   docker build -t $DOCKER_REGISTRY/flask-app:latest .
   docker push $DOCKER_REGISTRY/flask-app:latest
   ```

3. Deploy Prometheus (kube-prometheus-stack):

   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo update
   helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
     -n observability-demo \
     -f kubernetes/prometheus/values.yaml
   ```

4. Deploy Loki stack:

   ```bash
   helm repo add grafana https://grafana.github.io/helm-charts
   helm repo update
   helm install loki grafana/loki-stack \
     -n observability-demo \
     -f kubernetes/loki/values.yaml
   ```

5. Deploy Grafana:

   ```bash
   helm install grafana grafana/grafana \
     -n observability-demo \
     -f kubernetes/grafana/values.yaml
   ```

6. Deploy sample app and alerts:

   ```bash
   kubectl apply -f kubernetes/sample-app/deployment.yaml
   kubectl apply -f kubernetes/sample-app/service.yaml
   kubectl apply -f alerts/app-alerts.yaml
   ```

## Accessing UIs

- Grafana:

  ```bash
  kubectl port-forward svc/grafana -n observability-demo 3000:80
  ```

  Visit `http://localhost:3000`, login with `admin` / `promgrafadmin`. [file:1]

- Prometheus and Loki UIs are available via their services using `kubectl port-forward`. 

## Verifying Metrics

In Prometheus UI, run: 

- `flask_app_requests_total`
- `histogram_quantile(0.99, sum by (le, endpoint) (rate(flask_app_request_latency_seconds_bucket[5m])))`

## Verifying Logs

In Grafana Explore (Loki datasource): 

- Query `{app="flask-app"}` and filter by labels like `level`, `endpoint`, `method`.

## Triggering HighLatencyAlert

Generate load or artificially slow the `/hello` endpoint (e.g., temporary sleep in code) to push P99 latency above 0.5s for > 1 minute.

You should see `HighLatencyAlert` firing in Alertmanager and delivered to your configured webhook. 

## Local Development

To run the sample app without K8s:

```bash
cd app
docker-compose up --build
```

Visit `http://localhost:5000/hello` and `http://localhost:5000/metrics`. 