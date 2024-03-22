# CLONE KEPLER SOURCE FILES FROM REPO
git clone --depth 1 https://github.com/sustainable-computing-io/kepler

# GENERATE DEPLOYMENT FILES FROM KEPLER ARGS
cd kepler
make tools
make build-manifest OPTS="PROMETHEUS_DEPLOY HIGH_GRANULARITY ESTIMATOR_SIDECAR_DEPLOY"

# DEPLOY GENERATED KEPLER MANIFESTS
kubectl apply -f _output/generated-manifest/deployment.yaml

# OBSERVE WHEN INSTALLS FINISH
kubectl get pods -A -w