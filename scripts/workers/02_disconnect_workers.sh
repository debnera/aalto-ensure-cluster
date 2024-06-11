kubectl drain worker1 --ignore-daemonsets
kubectl drain worker2 --ignore-daemonsets
kubectl drain worker3 --ignore-daemonsets
kubectl drain worker4 --ignore-daemonsets
kubectl drain worker5 --ignore-daemonsets


kubectl delete node worker1
kubectl delete node worker2
kubectl delete node worker3
kubectl delete node worker4
kubectl delete node worker5
