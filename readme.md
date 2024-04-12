## Repository Overview

- Create a `Kubernetes` cluster with baremetal hardware using six `NUC` machines:
    - One master node.
    - Five worker nodes.
    - No virtualized machines.
- Deploy a complete monitoring stack to observe the cluster's performance, including:
    - `Prometheus`: Metrics scraping.
    - `Kepler`: Energy metrics.
    - `Grafana`: Near-real time metrics dashboards.
- Perform controlled experiments remotely:
    - Feed image matricies into a `Kafka` message queue at controlled intervals via `Python` script.
    - Consume and process these matricies with `Yolo` models, deployed as `Kubernetes` pods.
        - `Kafka` provides automatic load balancing, regardless of how many consumers are deployed.
    - Feed inference statistics back into `Kafka`.
- Observe the experiment's progress and performance through `Grafana` dashboards.
- After an experiment concludes, create datasets from the generated metrics data in `Prometheus`.
- Attempt to find patterns and correlations from these datasets.

<!-- ########################################################################################################## -->
## Table of Contents (sub dirs)

<!-- ########################################################################################################## -->
### 1. [Install `Ubuntu` dependencies](#)

<!-- ########################################################################################################## -->
### 2. [Create the `Kubernetes` cluster with `KubeADM`](#)

<!-- ########################################################################################################## -->
### 3. [Deploy a Monitoring Stack to track the cluster's resource usage](#)

<!-- ########################################################################################################## -->
### 4. [Deploy the `Kafka` message queue](#)

<!-- ########################################################################################################## -->
### 5. [Create and deploy `Yolo` consumers](#)

<!-- ########################################################################################################## -->
### 6. [Create & start the data producer](#)

<!-- ########################################################################################################## -->
### 7. [Connect remotely & setup experiment environment](#)

<!-- ########################################################################################################## -->
### 8. [Extract `Prometheus` contents into a dataset](#)
