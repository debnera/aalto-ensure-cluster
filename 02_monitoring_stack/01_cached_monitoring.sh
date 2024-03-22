# DEPLOY KUBE FILES
kubectl apply --server-side -f cached_monitoring/setup/
kubectl wait --for condition=Established --all CustomResourceDefinition --namespace=monitoring
kubectl apply -f cached_monitoring/

# OBSERVE WHEN INSTALLS FINISH
kubectl get pods -A -w