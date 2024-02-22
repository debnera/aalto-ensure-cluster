kubectl apply --server-side -f deployments/setup/
kubectl wait --for condition=Established --all CustomResourceDefinition --namespace=monitoring
kubectl apply -f deployments/
