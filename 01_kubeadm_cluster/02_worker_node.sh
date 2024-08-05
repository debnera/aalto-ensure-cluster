# CREATE INSTALL FILE (COPY THIS CONTENT INTO IT)
# sudo nano create_worker.sh && sudo chmod +x create_worker.sh && sudo ./create_worker.sh

# TURN OFF LINUX SWAP & FIREWALL
sudo swapoff -a
sudo systemctl stop firewalld
sudo systemctl disable firewalld

# SET THESE VARIABLES TO YOUR GENERATED VALUES
MASTER_IP="192.168.1.152"
JOIN_TOKEN="hzg98m.s8o5a37sg485db07"
SHA_TOKEN="8fbc2686a7f850b103e73482da1ab1df553516e1dc745029598e7e58b8e4b5f4"

# JOIN THE CLUSTER
kubeadm join $MASTER_IP:6443 \
    --token $JOIN_TOKEN \
    --discovery-token-ca-cert-hash sha256:$SHA_TOKEN \
    --cri-socket=unix:///var/run/cri-dockerd.sock

# RENAME THE WORKER NODE ON MASTER
# kubectl get pods -A -w
# kubectl label nodes worker1 kubernetes.io/role=worker
# kubectl get nodes -w
