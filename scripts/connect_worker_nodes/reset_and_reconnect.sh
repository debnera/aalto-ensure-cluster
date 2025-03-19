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
