scp kube.token wickstjo@worker1:~/
scp kube.token wickstjo@worker2:~/
scp kube.token wickstjo@worker3:~/
scp kube.token wickstjo@worker4:~/
scp kube.token wickstjo@worker5:~/

scp reset_and_reconnect.sh wickstjo@worker1:~/
scp reset_and_reconnect.sh wickstjo@worker2:~/
scp reset_and_reconnect.sh wickstjo@worker3:~/
scp reset_and_reconnect.sh wickstjo@worker4:~/
scp reset_and_reconnect.sh wickstjo@worker5:~/

ssh wickstjo@worker1 ./reset_and_reconnect.sh
kubectl get nodes
ssh wickstjo@worker2 ./reset_and_reconnect.sh
kubectl get nodes
ssh wickstjo@worker3 ./reset_and_reconnect.sh
kubectl get nodes
ssh wickstjo@worker4 ./reset_and_reconnect.sh
kubectl get nodes
ssh wickstjo@worker5 ./reset_and_reconnect.sh
kubectl get nodes
