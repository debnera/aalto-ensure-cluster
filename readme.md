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
  - Something has changed in the latest versions, causing Kepler to fail to launch with old configuration files.
  - Fixed by setting Kepler to use some older version (TODO: Try to find the exact latest version which works)
  - This was with the "cached kepler", maybe "fresh kepler" would have worked without changes. However, does this also reset configs?

- Add more flexibility to which cloud service is used for remote work
  - e.g., use environment variable $CLOUD which can be set in the user's .bashrc to automatically load it.

- Add more helper scripts to make management easier
- Small improvements to readmes
- Small adjustments to scripts
  - extractor.py was slightly broken with imports (pad_print not imported from utilz.py)
  - data feeder script was slightly broken (typo in code)

## Some basic commands to get started

`kubectl get nodes -o wide`  # list all connected workers

`kubectl get pods -A -o wide`  # list all pods running on all workers

`kubectl logs`   # get stdout for specific pod

`kubectl logs yolo-consumer-fb5b465df-jchkv -n workload`  # get stdout for a specific pod under namespace 'workload'

`kubectl apply application.yaml`  # deploy application (automatically creates pods on workers)

`kubectl delete -f application.yaml`  # undeploy application (automatically terminates pods)

`screen -ls`  # list screens from current user

`sudo ls -laR /var/run/screen/`  # List all screens running from all users


## 99% Success Rate Experiment Operation Guide: The Bare Minimums Step-by-step

BEFORE YOU START: 
01, 02, 03,... will refer to the sub directories `01_kubeadm_cluster`, `02_monitoring_stack`, and so on
If at any point something is not working, see the Troubleshooting section, and you might just find a solution 

- Part 1: Reset Everything (just to be safe)
  - Run `docker compose down` in 05 resetting yolo data collection.
  - Run `02_shutdown.sh` in 03 to shutdown any active Kafka related programs.
  - Run `99_reset_master.sh` in 01 to reset the master and control plane.
  - Run `docker ps`, and remove any straggling containers, if any using `docker rm <container-id> -f`.

- Part 2: Cluster Software Stack Up and Running

  - Run `01_master_node.sh` in 01 to start up the control plane.
  - Run `00_create_new_kube_token.sh` and `01_reset_and_connect_workers.sh` in scripts/workers/ to get workers connected (For univeristy cluster: Make sure to use password 'pass' when asked for wickstjo).
  - You should now be able to see all five workers connected using `kubectl get nodes`.
  - Run `01_cached_monitoring.sh` and `02_cached_monitoring.sh` in 02 to setup prometheus, kepler, and grafana.
  - Run `03_expose_ports.sh` in 02 to activate port forwarding from Kube.
  - Make sure that you can access grafana at localhost:3000 and login (For university cluster: username: admin, password: admin).
  - Once logged in, you can import a dashboard from the top right, (ensure_project.json from 02/grafana_dasboards/ is a good choice) and make sure that some power readings are visible.
  - Also check that prometheus at localhost:9090 displays some data in the graph, when you search for any 'kepler_' metric.
  - Run `04_metrics_server.sh` to allow for kube to scale pods up and down.

- Part 3: Kafka, Workload, and Workload Monitoring

  - If it's your first time running the cluster or get some permission errors, first create a 'db_prometheus' named folder and run `00_set_permissions.sh` in 03.
  - Run `01_launch_local_kafka.sh` in 03 and then press enter when asked about deleting cached data.
  - Check the ensure_cluster dashboard in graphana to see that kafka data can be read.
  - If you have made changes to your workload consumer app scripts or it is your first time running the cluster:
    - Run `01_build_and_test.sh` in 04, making sure that the dockerfile and other names in the script are the ones you wish to run.
    - Run `02_refresh_image.sh` in 04, making sure that you are logged in to dockerhub and your username and the image name are correct in the script.
  - Run `03_init_and_deploy.sh` in 04, with the number of consumers you wish for the kafka broker to listen to as an argument. A good choice is 5. Press enter once the script tells you that it is ready to deploy.
  - Run `kubectl get pods -A -o wide` to check that the pods are being deployed with no problems.
  - Run `00_example_yolo_tracker.sh` in 05 if you wish to save yolo qos data.


- Part 4: Running the Experiment
  - Edit `01_example_short_experiment.sh` in 05 to your desired parameters, most likely only --max_mbps and --duration.
  - Run `01_example_short_experiment.sh` in 05.
  - Check that raw image workload data is being pushed to Kafka via grafana. You should see the BytesIn (green) increasing.
  - Check that processed image output data is being pushed to Kafka via grafana. The BytesOut (yellow) should be increasing.
  - Check the command line window where you ran the `00_example_yolo_tracker.sh` script to see if yolo qos outputs are measured.


- Part 5: Extracting Yolo and Prometheus Data
  - Data can be extracted once the experiment duration has passed
  - For Yolo
    - In 05, open app/yolo_outputs/ to find yolo qos data saved as .csv files.
    - Make sure to reset the yolo_tracker app via `docker compose down` then `docker compose up` when running a new run. It is wise to also save and clear the old data in the 'yolo_outputs' folder.
  - For Prometheus
    - In 07, run `python3 extrator.py --start "2024-01-30 19:10:15" --end "2024-01-31 03:10:15" --sampling 5 --n_threads 8 --segment_size 2000` to extract all prom data into app/snapshots/, making sure to modifty --start and --end based on the Local Time of your experiment run. A folder with a timestamp of extraction should appear, filled with metrics.  

- Troubleshooting
  - Access/sudo problem
    - If you have trouble accessing scripts, using `chmod` will likely solve the problem.
  - pod crashing problem
    - Likely there is a problem with the python scripts within the container, and thus looking at the logs of a specific error pod can help, see 'Some basic commands to get started' above.
  - Terminating namespace stuck problem
    - Often happens after running the command `kubectl delete -f application.yaml`, and can be fixed via https://www.ibm.com/docs/en/cloud-private/3.2.0?topic=console-namespace-is-stuck-in-terminating-state.
  - python script dependencies problem
    - make sure to know that some python scripts will be run on the docker container python environment while others on the master machine, so be sure that all requirements are up to date on both accordingly.  
  - kafka partitioning stuck problem
    - If running `03_init_and_deploy.sh` seems to get stuck on parititoning, restarting the kafka server using `02_shutdown.sh` in 03, and then `01_launch_local_kafka.sh` should solve the problem. Remember to also reconnect the yolo_tracker if you wish for yolo qos statistics.
  - empty prometheus extract snapshot data problem
    - remember to use the local time of your prometheus database when running the `extractor.py` script. It is also possible that the data got wiped due to a. restarting of the PC, b. the 48 hour timeout of prometheus, or c. a prometheus database restart via kubernetes actions.
  - Daemon socket problem
    - A common error you may face is the message 'permission denied while trying to connect to the Docker daemon socket at ...' This can occur when some of the kubernetes configurations are done with the 'sudo' prefix, while others are not, causing network related errors. To prevent this, completely restarting and making sure to not use 'sudo' unless aboslutely necessary should solve this problem. 
  - Network (grafana or port forwarding) problem
    -  Signs of this issue include, data from within kubernetes is struggling to load onto the grafana dashboards and broken pipe errors found when looking at `03_expose_ports.sh` using `screen -ls`.
    - Resetting the switch power and restarting the cluster may help, but overall this error has been quite mysterious and has only really been solved with time.  

## Unknown things

- Why is local kafka (that is used in the experiment) consuming significant amount of master node CPU while idling?
  - Seems to be linked to Prometheus2 scraping (interval is set to 1s)
  - 5s interval consumes significantly less resources
  - The culprits are three Java-processes running under wickstjo
    - For some reason they run under wickstjo, even if launched by someone else...?
- How to use Kepler model server?
- How to add custom things to prometheus / grafana? (e.g., experiment tracker output from python script)


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
