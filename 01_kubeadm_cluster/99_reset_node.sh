# CREATE INSTALL FILE (COPY THIS CONTENT INTO IT)
# sudo nano 99_reset_node.sh && sudo chmod +x 99_reset_node.sh && sudo ./99_reset_node.sh

# RESET THE NODES KUBEADM SETUP & NUKE ALL OLD KUBERNETES FILES
sudo kubeadm reset --cri-socket=unix:///var/run/cri-dockerd.sock
sudo rm -rf ~/.kube

# TURN OFF LINUX SWAP & FIREWALL
sudo swapoff -a
sudo systemctl stop firewalld
sudo systemctl disable firewalld

# SET THE NECESSARY VARIABLES
MASTER_IP="192.168.1.152"
JOIN_TOKEN="eyly0u.xisykck7t3kj5i4e"
SHA_TOKEN="671fe2eee2c3a033401bacc8f1465614d10242057aa7420b6b15629f4aeeebeb"

# JOIN THE CLUSTER
kubeadm join $MASTER_IP:6443 \
    --token $JOIN_TOKEN \
    --discovery-token-ca-cert-hash sha256:$SHA_TOKEN \
    --cri-socket=unix:///var/run/cri-dockerd.sock