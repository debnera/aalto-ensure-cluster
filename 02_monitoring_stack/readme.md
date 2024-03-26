## 1. DEPLOY PROMETHEUS & GRAFANA MONITORING STACK

- Deploy cached (modified) files: [`./01_cached_monitoring.sh`](01_cached_monitoring.sh)

```bash
kubectl apply --server-side -f cached_monitoring/setup/
kubectl wait --for condition=Established --all CustomResourceDefinition --namespace=monitoring
kubectl apply -f cached_monitoring/
```

- Generate fresh deployment files: [`./01_fresh_monitoring.sh`](01_fresh_monitoring.sh)

```bash
# CLONE THE PROMETHEUS & GRAFANA DEPLOYMENT FILES FROM REPO
git clone --depth 1 https://github.com/prometheus-operator/kube-prometheus
```

```bash
kubectl apply --server-side -f kube-prometheus/manifests/setup
kubectl wait --for condition=Established --all CustomResourceDefinition --namespace=monitoring
kubectl apply -f kube-prometheus/manifests/
```

## 2. DEPLOY KEPLER NODE MONITORS

- Deploy cached (modified) files: [`./02_cached_kepler.sh`](02_cached_kepler.sh)

```bash
# DEPLOY GENERATED KEPLER MANIFESTS
kubectl apply -f cached_kepler/deployment.yaml
```

- Generate fresh deployment files: [`./02_fresh_kepler.sh`](02_fresh_kepler.sh)

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

## 3. KUBERNETES METRICS SERVER

- Allows kubernetes to track the resource usage of individual pods.
- Required for dynamic service scaling.

```bash
kubectl apply -f kube_metrics_server.yaml
```

## 4. GRAFANA DASHBOARDS

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

## 99. KUBERNETES PORT FORWARDS & CLOUD PROXIES

- Once deployed, `Grafana` is available at port `3000`.
- Once deployed, `Prometheus` is available at port `9090`.
- The master node's network may be blocked to outsiders by a firewall.
    - This prevents you from directly `SSH`-ing to the cluster.
    - Instead, we tunnel through a cloud proxy.
- Quality of Life:
    - Use port forwarding screens to make these services **locally** available through the master node.
    - Make these services **publically** available through a cloud proxy.
    - [`./monitoring_port_forwards.sh`](monitoring_port_forwards.sh)

```bash
# EXAMPLE VARIABLES
MASTER_IP="192.158.1.38"
CLOUD_PROXY="user@myvm.northeurope.cloudapp.azure.com"

# KUBERNETES SERVICE PORT FORWARDS
screen -dmS grafana_pf kubectl -n monitoring port-forward svc/grafana 3000 --address=$MASTER_IP
screen -dmS prometheus_pf kubectl -n monitoring port-forward svc/prometheus-k8s 9090 --address=$MASTER_IP

# CREATE PORT FORWARDS TO CLOUD PROXY
screen -dmS grafana_pf ssh -R 3000:$MASTER_IP:3000 $CLOUD_PROXY
screen -dmS prometheus_pf ssh -R 9090:$MASTER_IP:9090 $CLOUD_PROXY
```

- To port forward these services to your home machine:
- [`./home_port_forwards.sh`](home_port_forwards.sh)

```bash
# EXAMPLE VARIABLE
CLOUD_PROXY="user@myvm.northeurope.cloudapp.azure.com"

# MIRROR CLOUD_PROXY:PORT TO LOCALHOST:PORT
screen -dmS grafana_proxy ssh -L 3000:localhost:3000 $CLOUD_PROXY
screen -dmS prometheus_proxy ssh -L 9090:localhost:9090 $CLOUD_PROXY
```