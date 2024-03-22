# CONNECT VIA SSH, THEN CHANGE THE HOSTNAME -- baseline_machine
# sudo nano /etc/hostname && sudo nano /etc/hosts
# sudo reboot

# CREATE INSTALL FILE
# sudo nano create_master.sh && sudo chmod +x create_master.sh && ./create_master.sh

# TURN OF SWAP & FIREWALLS
sudo swapoff -a
systemctl stop firewalld
sudo systemctl disable firewalld

# DEBUG: INVERSE THE PREVIOUS ACTIONS
# sudo swapon -a
# systemctl start firewalld
# sudo systemctl enable firewalld

# INITIALIZE THE CLUSTERS CONTROL PLANE (MASTER NODE)
sudo kubeadm init \
  --cri-socket=unix:///var/run/cri-dockerd.sock \
  --pod-network-cidr=10.0.0.0/8

echo -e "\n#####################################\n"

# MAKE THE NODE AVAILABLE
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# INSTALL POD NETWORK ADDON
# calico-kube-controllers IS GENERALLY THE LAST POD TO FINISH
curl https://raw.githubusercontent.com/projectcalico/calico/v3.26.3/manifests/calico.yaml -O
kubectl apply -f calico.yaml
kubectl get pods -A --watch

echo -e "\n#####################################\n"

# FINALLY, PRINT CLUSTER JOIN STRING
clear && kubectl get pods -A
kubeadm token create --print-join-command

# kubectl label nodes worker1 kubernetes.io/role=worker
# kubectl get nodes
# kubectl get pods -A -w





















# ADD THE FOLLOWING PROPS TO THE KUBE CONFIG
# sudo nano /etc/kubernetes/admin.conf
# echo "authentication:" | cat >> /etc/kubernetes/admin.conf

# authentication:
#   webhook: true
# authorization:
#   mode: Webhook

# RESTART KUBELET TO MAKE CHANGES TAKE PLACE
# sudo systemctl restart kubelet
