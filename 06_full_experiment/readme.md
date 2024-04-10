## Table of Contents

1. [Subdir Overview (TODO)](#)
2. [Connect to the Cluster Remotely](#)
3. [Port forward Monitoring Stack to remote location](#)
3. [Setup Experiment Screens](#)
    1. [Kafka Screen](#)
    2. [Deployment Screen](#)
    2. [Feeding Screen](#)

<!-- ########################################################################################################## -->

## 1. Subdir Purpose

<!-- ########################################################################################################## -->

## 2. Connect to the Cluster Remotely
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

<!-- ########################################################################################################## -->

## 3. Port forward Monitoring Stack to remote location

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

## 4. Setup Experiment Screens

#### 4.1 Kafka Screen
---

- Before every new experiment, you should kill your old `Kafka` and create a new one.
    - This makes sure there are no artifacts left in the topics.
- To do this, `CTRL+C` and execute the `run script` again.

```bash
# CREATE THE SCREEN ONCE
screen -S exp_kafka

# BOOT UP KAFKA FROM DOCKER, LIKE CHAPTER 3 DESCIRBED
cd aalto_ensure/kafka/docker
./run.sh
```

#### 4.2 Deployment Screen
---

- `Kafka` tends to react unpredictably when you push lots of data into a topic that doesn't already exist.
    - The topic will be created automatically.
    - Partition assignment may be wonky and slow.
- To fix this, we run a script that:
    1. Creates `n` temporary `Kafka` producers and consumers.
    2. Each producer sends one message to their designated consumer.
    3. After every consumer confirms, each topic partition has been initialized and tested.
- Now we can safely deploy our `Kubernetes` pods.

```bash
# CREATE THE SCREEN ONCE
screen -S exp_deployment

# THIS WILL TEST FOR FIVE TOPIC PARTITIONS
./aalto_ensure/04_yolo_consumer/03_init_and_deploy.sh 5
```

#### 4.3 Feeding Screen
---

- Before you start, make sure that:
    - `Kafka` has been deployed successfully.
    - The `Kubernetes` pods are been deployed successfully.
        - I confirm this via `Grafana` dashboards.
- This window must be active for the duration of the experiment.
    - Once the script is started, suspend the screen with `CTRL+A+D`
    - Note that you can enter the screen again with `screen -r exp_feeding`
- By stopping the script with `CTRL+C`, the helper threads die gracefully.


```bash
# CREATE THE SCREEN ONCE
screen -S exp_feeding

# PATH TO THE RELEVANT DIR
cd aalto_ensure/05_yolo_producer/app
```

```bash
# SET THE FEEDING PARAMETERS
EXP_DURATION=28800
EXP_BREAKPOINTS=800
EXP_MAX_MBPS=14
EXP_CYCLES=6

# RUN THE SCRIPT
python3 feeder.py
    --duration $EXP_DURATION
    --breakpoints $EXP_BREAKPOINTS
    --max_mbps $EXP_MAX_MBPS
    --n_cycles $EXP_CYCLES
```