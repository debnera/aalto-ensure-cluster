### 1. DEPLOY PROMETHEUS & GRAFANA MONITORING STACK

```bash
# CLONE THE PROMETHEUS & GRAFANA DEPLOYMENT FILES FROM REPO
git clone --depth 1 https://github.com/prometheus-operator/kube-prometheus
```

```bash
# DEPLOY IT VIA MANIFESTS
kubectl apply --server-side -f kube-prometheus/manifests/setup
kubectl wait --for condition=Established --all CustomResourceDefinition --namespace=monitoring
kubectl apply -f kube-prometheus/manifests/
```

```bash
# OBSERVE WHEN INSTALLS FINISH
kubectl get pods -A -w
```

### 99. DEPLOY KEPLER NODE MONITORS


```bash
# CLONE KEPLER SOURCE FILES FROM REPO
git clone --depth 1 https://github.com/sustainable-computing-io/kepler
```

```bash
# GENERATE DEPLOYMENT FILES FROM KEPLER ARGS
cd kepler
make tools
make build-manifest OPTS="PROMETHEUS_DEPLOY HIGH_GRANULARITY ESTIMATOR_SIDECAR_DEPLOY"
```

```bash
# DEPLOY GENERATED KEPLER MANIFESTS
kubectl apply -f _output/generated-manifest/deployment.yaml
```

```bash
# OBSERVE WHEN INSTALLS FINISH
kubectl get pods -A -w
```