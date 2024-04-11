## Repository Overview

- Create a `Kubernetes` cluster with baremetal hardware using six `NUC` machines:
    - One master node.
    - Five worker nodes.
    - No virtualized machines.
- Deploy a complete monitoring stack to observe the cluster's performance, including:
    - `Prometheus`: Metrics scraping.
    - `Grafana`: Near-real time dashboards.
    - `Kepler`: Energy metrics.
- Perform controlled experiments remotely:
    - Feed image matricies into a `Kafka` message queue at controlled intervals via `Python` script.
    - Consume and process these matricies with `Yolo` models, deployed as `Kubernetes` pods.
        - `Kafka` provides automatic load balancing, regardless of how many consumers are deployed.
    - Feed inference statistics back into `Kafka`.
- Observe the experiment's progress and performance through `Grafana` dashboards.
- After an experiment concludes, create datasets from the generated metrics data in `Prometheus`.
- Attempt to find patterns and correlations from these datasets.

<!-- ########################################################################################################## -->
## 1. [Install `Ubuntu` dependencies](#)

- Technically many Linux distros could work
- `Kepler` requires very specific kernel versions.
- `Ubuntu` is exceptionally heavy, and there are almost certainly better choices.
    - We tried `CentOS`, but it did not work out.
- Kubernetes clusters require multiple components:
    - `Kubelet`
    - `KubeADM`
    - `KubeCTL`

<!-- ########################################################################################################## -->
## 2. [Create the `Kubernetes` cluster with `KubeADM`](#)

- Create a master node, or control plane, that allows other nodes to join the cluster.
- Create worker nodes and add them to the cluster.
- Demonstrate how to reset a node.

<!-- ########################################################################################################## -->
## 3. [Deploy a Monitoring Stack to track the cluster's resource usage](#)

- Deploy systems that allow close monitoring of the cluster's resources:
    - `Prometheus` for scraping and temporarily storing metrics data.
    - `Grafana` for observing the metrics in near-real time through customizable dashboards.
- Deploy `Kepler` modules on each cluster node, allowing the tracking of energy usage.
- Deploy a `Kubernetes Metrics Server` to allow the cluster to dynamically scale pods.

<!-- ########################################################################################################## -->
## 4. [Deploy the `Kafka` message queue](#)

<!-- - Create a `Kafka` message queue and initialize input and output topics for the experiments.
    - The workload of a `Kafka` topic is automatically load balanced over its consumers.
    - This allows `Kubernetes` to scale services freely with minimal disruption. -->

<!-- ########################################################################################################## -->
## 5. [Create and deploy `Yolo` consumers](#)



<!-- ########################################################################################################## -->
## 6. [Create & start the data producer](#)



<!-- ########################################################################################################## -->
## 7. [Connect remotely & setup experiment environment](#)



<!-- ########################################################################################################## -->
## 8. [Extract `Prometheus` contents into a dataset](#)

