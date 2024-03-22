# CLONE SOURCE FILES FROM REPO
git clone --depth 1 https://github.com/prometheus-operator/kube-prometheus

# DEPLOY KUBE FILES
kubectl apply --server-side -f kube-prometheus/manifests/setup
kubectl wait --for condition=Established --all CustomResourceDefinition --namespace=monitoring
kubectl apply -f kube-prometheus/manifests/

# OBSERVE WHEN INSTALLS FINISH
kubectl get pods -A -w