# CREATE INSTALL FILE (COPY THIS CONTENT INTO IT)
# sudo nano 99_reset_node.sh && sudo chmod +x 99_reset_node.sh && sudo ./99_reset_node.sh

# RESET THE NODES KUBEADM SETUP & NUKE ALL OLD KUBERNETES FILES
sudo kubeadm reset --cri-socket=unix:///var/run/cri-dockerd.sock
sudo rm -rf ~/.kube