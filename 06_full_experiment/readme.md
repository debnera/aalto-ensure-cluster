## 1. CONNECT TO THE CLUSTER REMOTELY
```bash
# CONNECT TO THE CLOUD PROXY
ssh ansure@ansurevm.northeurope.cloudapp.azure.com

# CONNECT TO THE MASTER NODE
ssh -p 2222 wickstjo@localhost
```

- From here, you can connect to any worker node.
- Use  their respective IP or network alias:
    - Aliases listed in: `/etc/hosts`

```bash
# WORKER 1
ssh 130.233.193.143
ssh worker1

# WORKER 2
ssh 130.233.193.147
ssh worker2

# WORKER 3
ssh 130.233.193.60
ssh worker3

# WORKER 4
ssh 130.233.193.124
ssh worker4

# WORKER 5
ssh 130.233.193.63
ssh worker5
```

## 2. PORT FORWARD MONITORING STACK TO REMOTE LOCATION

- Script location: [`./01_cluster_port_forwards.sh`](01_cluster_port_forwards.sh)
- Use port forwarding screens to make these services **locally** available through the master node.
- Then make these services **publically** available through a cloud proxy.

```bash
# THESE VARS MIGHT CHANGE
MASTER_IP="130.233.193.117"
CLOUD_PROXY="ansure@ansurevm.northeurope.cloudapp.azure.com"

# KUBERNETES SERVICE PORT FORWARDS
screen -dmS grafana_pf kubectl -n monitoring port-forward svc/grafana 3000 --address=$MASTER_IP
screen -dmS prometheus_pf kubectl -n monitoring port-forward svc/prometheus-k8s 9090 --address=$MASTER_IP

# CREATE PORT FORWARDS TO CLOUD PROXY
screen -dmS grafana_pf ssh -R 3000:$MASTER_IP:3000 $CLOUD_PROXY
screen -dmS prometheus_pf ssh -R 9090:$MASTER_IP:9090 $CLOUD_PROXY
```

- Script location: [`./02_home_port_forwards.sh`](02_home_port_forwards.sh)
- Run the following script from your home machine to make the services available to you:
    - `Prometheus` runs on port `localhost:9090`
    - `Grafana` runs on port `localhost:3000`

```bash
# THESE VARS MIGHT CHANGE
CLOUD_PROXY="ansure@ansurevm.northeurope.cloudapp.azure.com"

# MIRROR CLOUD_PROXY:PORT TO LOCALHOST:PORT AT HOME
screen -dmS grafana_proxy ssh -L 3000:localhost:3000 $CLOUD_PROXY
screen -dmS prometheus_proxy ssh -L 9090:localhost:9090 $CLOUD_PROXY
```

## SETUP EXPERIMENT SCREENS

#### KAFKA SCREEN
<!-- ```bash
# CREATE THE SCREEN
screen -S exp_kafka

# BOOT UP KAFKA FROM DOCKER, LIKE CHAPTER 3 DESCIRBED
./aalto-ensure/kafka/docker/run.sh
``` -->

#### KUBERNETES SCREEN

#### FEEDING SCREEN



<!--
```bash

```
-->