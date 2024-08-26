## Overview

- Create a master node, or control plane, that allows other nodes to join the cluster.
- Create worker nodes and add them to the cluster.
- Demonstrate how to reset a node.

<!-- ########################################################################################################## -->
## Table of Contents

1. [Create a `Kubernetes` master node/control plane.](#)
2. [Create worker nodes & add it to the cluster.](#)
9. [Reset a cluster node & rejoin the cluster.](#)

<!-- ########################################################################################################## -->
## 1. CREATE A KUBERNETES MASTER NODE

- Script location: [`./01_master_node.sh`](01_master_node.sh)
- Individual script steps:

```bash
# TURN OF SWAP & FIREWALLS
sudo swapoff -a
systemctl stop firewalld
sudo systemctl disable firewalld
```

```bash
# INITIALIZE THE CLUSTERS CONTROL PLANE (MASTER NODE)
sudo kubeadm init \
  --cri-socket=unix:///var/run/cri-dockerd.sock \
  --pod-network-cidr=10.0.0.0/8
```

```bash
# CLONE CONFIGS & MAKE THE CONTROL PLANE AVAILABLE TO OTHERS
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

```bash
# FIND THE RIGHT VERSION FOR YOU
CALICO_TARGET="https://raw.githubusercontent.com/projectcalico/calico/v3.26.3/manifests/calico.yaml"

# INSTALL A POD NETWORK ADDON
# THIS IS NECESSARY FOR KUBE PODS TO FIND EACH OTHER
# WE ARE USING "CALICO"
curl $CALICO_TARGET -O
kubectl apply -f calico.yaml
```

```bash
# WAIT FOR EVERYTHING TO INSTALL
# GENERALLY, "calico-kube-controllers" WILL BE THE LAST ONE
kubectl get pods -A --watch
```

```bash
# FINALLY, PRINT THE CLUSTERS' "JOIN STRING"
# THIS IS UNIQUE AND NECESSARY FOR WORKERS NODES TO JOIN THE CLUSTER
kubeadm token create --print-join-command
```

<!-- ########################################################################################################## -->
## 2. CREATE AND CONNECT KUBERNETES WORKER NODES

- Old method was to individually add each worker
- Now we can add all the workers at once by running 
- 1. [`../scripts/workers/00_create_new_kube_token.sh`](00_create_new_kube_token.sh)

```bash
kubeadm token create --print-join-command > kube.token
echo "Printed the join command and token to 'kube.token'. You can now use it to connect the workers."
```

- 2. [`../scripts/workers/01_reset_and_connect_workers.sh`](01_reset_and_connect_workers.sh)

```bash
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
```

- The script above uses the following helper script [`../scripts/workers/reset_and_reconnect.sh`](reset_and_reconnect.sh) 

```bash
# RESET THE NODE
sudo -S kubeadm reset --cri-socket=unix:///var/run/cri-dockerd.sock

# NUKE ALL OLD KUBERNETES FILES
sudo -S rm -rf /home/wickstjo/.kube

# TURN OFF LINUX SWAP & FIREWALL
sudo -S swapoff -a
sudo -S systemctl stop firewalld
sudo -S systemctl disable firewalld

echo -e "\n#####################################\n"

JOIN_CMD=$(cat /home/wickstjo/kube.token)

sudo -S $JOIN_CMD --cri-socket=unix:///var/run/cri-dockerd.sock
```

<!-- ########################################################################################################## -->
## 99. RESET CLUSTER

- The fastest way to reset the cluster is to reset the master via:
- [`./99_reset_master.sh`](99_reset_master.sh)