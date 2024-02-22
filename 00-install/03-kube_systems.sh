# CREATE INSTALL FILE
# sudo nano create_kube.sh && sudo chmod +x create_kube.sh && ./create_kube.sh

echo -e "\n#####################################\n"

# ADD KUBE COMPONENT CERTS
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

# This overwrites any existing configuration in /etc/apt/sources.list.d/kubernetes.list
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

echo -e "\n#####################################\n"

# INSTALL KUBE & FREEZE ITS VERSION
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl

# CHECK THAT EVERYTHING IS OK
kubelet --version
kubeadm version
# kubectl version