# CREATE INSTALL FILE (COPY THIS CONTENT INTO IT)
# sudo nano create_worker.sh && sudo chmod +x create_worker.sh && sudo ./create_worker.sh

# TURN OFF LINUX SWAP & FIREWALL
sudo swapoff -a
sudo systemctl stop firewalld
sudo systemctl disable firewalld

# JOIN THE CLUSTER
kubeadm join 192.168.1.152:6443 \
    --token eyly0u.xisykck7t3kj5i4e \
    --discovery-token-ca-cert-hash sha256:671fe2eee2c3a033401bacc8f1465614d10242057aa7420b6b15629f4aeeebeb \
    --cri-socket=unix:///var/run/cri-dockerd.sock

# RENAME THE WORKER NODE ON MASTER
# kubectl get pods -A -w
# kubectl label nodes worker1 kubernetes.io/role=worker
# kubectl get nodes -w