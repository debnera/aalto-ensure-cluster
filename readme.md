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

## Changelog
Compared to the original repository by John, we have fixed:

- Kepler fails to launch, because it tries to use the 'latest' version instead of some old version.
-- Something has changed in the latest versions, causing Kepler to fail to launch with old configuration files.
-- Fixed by setting Kepler to use some older version (TODO: Try to find the exact latest version which works)
-- This was with the "cached kepler", maybe "fresh kepler" would have worked without changes. However, does this also reset configs?

- Add more flexibility to which cloud service is used for remote work
-- e.g., use environment variable $CLOUD which can be set in the user's .bashrc to automatically load it.

- Add more helper scripts to make management easier

- Small adjustments to scripts
-- extractor.py was slightly broken with imports (pad_print not imported from utilz.py)
-- data feeder script was slightly broken (typo in code)

## Some basic commands to get started

`kubectl get nodes -o wide`  # list all connected workers

`kubectl get pods -A -o wide`  # list all pods running on all workers

`kubectl logs`   # get stdout for specific pod

`kubectl logs yolo-consumer-fb5b465df-jchkv -n workload`  # get stdout for a specific pod under namespace 'workload'

`kubectl apply application.yaml`  # deploy application (automatically creates pods on workers)

`kubectl delete -f application.yaml`  # undeploy application (automatically terminates pods)

`screen -ls`  # list screens from current user

`sudo ls -laR /var/run/screen/`  # List all screens running from all users


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
