### GENERAL NOTES:
- Once deployed, `Grafana` is available at port `3000`.
- Once deployed, `Prometheus` is available at port `9090`.
- Use port forwarding screens to make these services available through the master node:
    - `./monitoring_port_forwards.sh`

### 1. DEPLOY PROMETHEUS & GRAFANA MONITORING STACK

- Deploy cached (modified) files:
- `./02_monitoring_stack/01_cached_monitoring.sh`

```bash
kubectl apply --server-side -f cached_monitoring/setup/
kubectl wait --for condition=Established --all CustomResourceDefinition --namespace=monitoring
kubectl apply -f cached_monitoring/
```

- Generate fresh deployment files:
- `./02_monitoring_stack/01_fresh_monitoring.sh`

```bash
# CLONE THE PROMETHEUS & GRAFANA DEPLOYMENT FILES FROM REPO
git clone --depth 1 https://github.com/prometheus-operator/kube-prometheus
```

```bash
kubectl apply --server-side -f kube-prometheus/manifests/setup
kubectl wait --for condition=Established --all CustomResourceDefinition --namespace=monitoring
kubectl apply -f kube-prometheus/manifests/
```

### 2. DEPLOY KEPLER NODE MONITORS

- Deploy cached (modified) files:
- `./02_monitoring_stack/02_cached_kepler.sh`

```bash
# DEPLOY GENERATED KEPLER MANIFESTS
kubectl apply -f cached_kepler/deployment.yaml
```

- Generate fresh deployment files:
- `./02_monitoring_stack/02_fresh_kepler.sh`

```bash
# CLONE KEPLER SOURCE FILES FROM REPO
git clone --depth 1 https://github.com/sustainable-computing-io/kepler
```

```bash
# COMPILE BASELINE FILES
cd kepler
make tools

# GENERATE DEPLOYMENT MANIFESTS BASED ON KEPLER ARGS
# CONSULT KEPLERS' DOCS FOR MORE DETAILS
make build-manifest OPTS="PROMETHEUS_DEPLOY HIGH_GRANULARITY ESTIMATOR_SIDECAR_DEPLOY"
```

```bash
# DEPLOY GENERATED KEPLER MANIFESTS
kubectl apply -f _output/generated-manifest/deployment.yaml
```

### 3. KUBERNETES METRICS SERVER

- Allows kubernetes to track the resource usage of individual pods.
- Required for dynamic service scaling.

```bash
kubectl apply -f kube_metrics_server.yaml
```

### 4. GRAFANA DASHBOARDS

- `Grafana` links up with `Prometheus` to render real-time data dashboards.
- Dashboards are stored in a JSON format, and can be imported/exported through the web GUI.
- This repo contains a handful of dashboards that I have created/found useful:

```bash
Ensure Project:     grafana_dashboards/ensure_project.json

Node Exporter:      grafana_dashboards/node_exporter.json
Kube State:         grafana_dashboards/kube_state.json

Kafka Metrics:      grafana_dashboards/kafka_metrics.json
Kepler Metrics:     grafana_dashboards/kepler_metrics.json
```