# DEPLOY GENERATED KEPLER MANIFESTS
kubectl apply -f cached_kepler/deployment.yaml

# OBSERVE WHEN INSTALLS FINISH
kubectl get pods -A -w