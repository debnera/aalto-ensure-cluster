## Overview

- Technically many Linux distros could work
- `Kepler` requires very specific kernel versions.
- `Ubuntu` is exceptionally heavy, and there are almost certainly better choices.
    - We tried `CentOS`, but it did not work out.
- Kubernetes clusters require multiple components:
    - `Kubelet`
    - `KubeADM`
    - `KubeCTL`

<!-- ########################################################################################################## -->
## Table of Contents
1. [Install the baseline `Ubuntu` dependencies](#)
2. [Install `Docker`](#)
3. [Install `Docker-CRI`](#)
4. [Install the different `Kubernetes` cluster components](#)

<!-- ########################################################################################################## -->
## 1. INSTALL BASELINE UBUNTU DEPENDENCIES

- Script location: [`./00_ubuntu_init.sh`](00_ubuntu_init.sh)
- Individual script steps:

```bash
# FOR SSH-ING TO CLUSTER NODES
sudo apt-get install -y openssh-server openssh-client

# OTHER MISC DEPENDENCIES
sudo apt-get install -y nano git wget curl make gh net-tools make
```

<!-- ########################################################################################################## -->
## 2. INSTALL DOCKER

- Script location: [`./01_docker.sh`](01_docker.sh)
- Individual script steps:

```bash
# DOWNLOAD & INSTALL DOCKER
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh test-docker.sh
```

```bash
# SETUP DOCKER PERMISSIONS FOR LINUX
sudo usermod -aG docker $USER
newgrp docker

# START THE LINUX SERVICES
sudo systemctl enable docker.service
sudo systemctl enable containerd.service
```

```bash
# VERIFY THAT DOCKER WORKS
docker version
sudo docker run hello-world
```

<!-- ########################################################################################################## -->
## 3. INSTALL DOCKER-CRI (ALLOWS KUBERNETES TO USE DOCKER)

- Script location: [`./02_docker_cri.sh`](02_docker_cri.sh)
- Individual script steps:

```bash
# DOWNLOAD & INSTALL GO-LANG
wget https://go.dev/dl/go1.21.3.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.3.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
go version
```

```bash
# FOR PERSISTENT GO REFERENCE, ADD EXPORT TO BASHRC
sudo nano ~/.bashrc
echo "export PATH=$PATH:/usr/local/go/bin" | cat >> ~/.bashrc
```

```bash
# DOWNLOAD & INSTALL DOCKER CRI
# NECESSARY FOR KUBERNETES TO USE DOCKER
git clone https://github.com/Mirantis/cri-dockerd.git
cd cri-dockerd
make cri-dockerd
mkdir -p /usr/local/bin
```

```bash
# INSTALL THE CRI API
sudo install -o root -g root -m 0755 cri-dockerd /usr/local/bin/cri-dockerd
sudo install packaging/systemd/* /etc/systemd/system
sudo sed -i -e 's,/usr/bin/cri-dockerd,/usr/local/bin/cri-dockerd,' /etc/systemd/system/cri-docker.service
```

```bash
# ENABLE NEW SERVICES
sudo systemctl daemon-reload
sudo systemctl enable --now cri-docker.socket
```

<!-- ########################################################################################################## -->
## 4. INSTALL KUBERNETES COMPONENTS

- Script location: [`./03_kube_systems.sh`](03_kube_systems.sh)
- Individual script steps:

```bash
# ADD KUBE COMPONENT CERTS
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
```

```bash
# OVERWRITE OLD KUBE CONFIG IN /etc/apt/sources.list.d/kubernetes.list
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
```

```bash
# INSTALL KUBE COMPONENTS & FREEZE THEIR VERSIONS
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

```bash
# VERIFY THAT EVERYTHING WORKS
# KUBECTL CAN ONLY BE TESTED ONCE THE CLUSTER IS RUNNING
kubelet --version
kubeadm version
```