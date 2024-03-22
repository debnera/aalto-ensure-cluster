### 1. CREATE A KUBERNETES MASTER NODE

- `./01_kubeadm_cluster/01_master_node.sh`
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
# INSTALL A POD NETWORK ADDON
# THIS IS NECESSARY FOR KUBE PODS TO FIND EACH OTHER
# WE ARE USING "CALICO"
curl https://raw.githubusercontent.com/projectcalico/calico/v3.26.3/manifests/calico.yaml -O
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

### 2. CREATE A KUBERNETES WORKER NODE

- `./01_kubeadm_cluster/02_worker_node.sh`
- Individual script steps:

```bash
# TURN OF SWAP & FIREWALLS
sudo swapoff -a
systemctl stop firewalld
sudo systemctl disable firewalld
```

```bash
# SET THE NECESSARY VARIABLES
# THE TOKENS ARE GENERATED WHEN CREATING THE MASTER NODE
MASTER_IP="192.168.1.152"
JOIN_TOKEN="eyly0u.xisykck7t3kj5i4e"
SHA_TOKEN="671fe2eee2c3a033401bacc8f1465614d10242057aa7420b6b15629f4aeeebeb"
```

```bash
# JOIN THE CLUSTER
kubeadm join $MASTER_IP:6443 \
    --token $JOIN_TOKEN \
    --discovery-token-ca-cert-hash sha256:$SHA_TOKEN \
    --cri-socket=unix:///var/run/cri-dockerd.sock
```

### 99. RESET CLUSTER NODE

- `./01_kubeadm_cluster/99_reset_node.sh`
- Individual script steps:

```bash
# RESET THE KUBEADM SETUP & NUKE ALL OLD KUBERNETES FILES
# THIS NEEDS TO BE PERFORMED ON EACH NODE, MASTER AND WORKER ALIKE
sudo kubeadm reset --cri-socket=unix:///var/run/cri-dockerd.sock
sudo rm -rf ~/.kube
```

```bash
# TURN OFF LINUX SWAP & FIREWALL
sudo swapoff -a
sudo systemctl stop firewalld
sudo systemctl disable firewalld
```

```bash
# SET THE NECESSARY VARIABLES
# THE TOKENS ARE GENERATED WHEN CREATING THE MASTER NODE
MASTER_IP="192.168.1.152"
JOIN_TOKEN="eyly0u.xisykck7t3kj5i4e"
SHA_TOKEN="671fe2eee2c3a033401bacc8f1465614d10242057aa7420b6b15629f4aeeebeb"
```

```bash
# JOIN THE CLUSTER
kubeadm join $MASTER_IP:6443 \
    --token $JOIN_TOKEN \
    --discovery-token-ca-cert-hash sha256:$SHA_TOKEN \
    --cri-socket=unix:///var/run/cri-dockerd.sock
```