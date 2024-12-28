"""
Run_7: Day-night-cycle for all models adjusted to max throughput

- All models and resolutions
- Set max mbps for each model depending on their max capability
- But scale max mbps by 0.5

"""


import logging
import os
import socket
import subprocess
import time
import yaml
import create_deployment_yaml
from warehouse import burst_feeder
from warehouse import kafka_init
from warehouse.msg_to_csv import MessageToCSVProcessor
from warehouse.validate_results import ValidationThread
from data_extractor import extractor
import datetime
import argparse  # New import for argument parsing

# Argument parser for command-line arguments
parser = argparse.ArgumentParser(description="Run warehouse experiments with optional smoketest.")
parser.add_argument("--smoketest", action="store_true", help="Run a short smoketest.")

args = parser.parse_args()  # Parse arguments


feeder = burst_feeder
# feeder = burst_feeder  # Use linear_feeder or day_night_feeder
idle_before_start_1 = 120 # (seconds) Wait for application instances to receive their kafka assignments - otherwise might get stuck
idle_before_start_2 = 0.5 * 60  # (seconds) Additional wait after Kafka is verified working
idle_after_end = 0.5 * 60  # (seconds) Catch the tail of the experiment metrics
total_runtime_hours = 24
num_workers = [1, 2, 3, 4, 5, 6]  # Number of lidar workers (number of worker pods launched on cluster)
lidar_points = [1000, 5000, 10_000]  # Number of points in a single point cloud (Depends on dataset)
hours_per_model = total_runtime_hours / (len(num_workers) * len(lidar_points))
seconds_per_model = hours_per_model * 3600  # TODO: How to estimate and control time?
deploy_worker_template_path = "kubernetes_templates/worker_template.yaml"  # Template for running the experiments
deploy_worker_experiment_path = None  # This file will be created from the template
deploy_master_template_path = "kubernetes_templates/master_template.yaml"  # Template for running the experiments
deploy_master_experiment_path = None  # This file will be created from the template
# kafka_servers = 'localhost:10001,localhost:10002,localhost:10003'  # Servers for local testing
kafka_servers = "130.233.193.117:10001"  # Servers for running on our cluster
num_workers = 4
namespace = "workloadc"
worker_name = "lidar-worker"
master_name = "lidar-master"
kube_application_names = [worker_name, master_name]


logging.basicConfig(
    filename=f'{time.time()}_experiment.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

def log(message):
    logging.info(message)
    print(message)

# Apply smoketest modifications if --smoketest argument is provided
if args.smoketest:
    log("Applying smoketest modifications for a short debugging run...")
    try:
        # Kube might not like localhost -> need to get the actual ip of the local setup
        log(f"Retrieving local ip to enable Kafka<->Kubernetes communication...")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
        kafka_servers = f"{local_ip}:10001"
        log(f"Setting Kafka ip to {kafka_servers}")
    except Exception as e:
        log(f"Error fetching local IP: {e} -> using localhost instead")
        kafka_servers = "localhost:10001"

    experiment_duration = 60  # Short experiment duration
    idle_before_start_2 = 10  # Shorter wait times
    idle_after_end = 10
    num_workers = [4]  # Only one experiment
    lidar_points = [1000]  # Only one experiment


def scale_and_wait_for_replicas(num_replicas, application_name):
    # Start scaling the application
    subprocess.run(
        ["kubectl", "scale", "deployment", f"{application_name}", "-n", f"{namespace}", f"--replicas={num_replicas}"])
    # Wait for the application to scale
    while True:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", f"{namespace}", "-l", f"run={application_name}", "-o", "yaml"],
            capture_output=True,
            text=True
        )
        pods = yaml.safe_load(result.stdout)
        running_pods = [pod for pod in pods["items"] if pod["status"]["phase"] == "Running"]
        if len(running_pods) == num_replicas:
            break
        log(f"Waiting for {len(running_pods)}/{num_replicas} {application_name} pods to be running...")
        time.sleep(5)  # Wait for 10 seconds before checking again


def wait_for_terminate(num_replicas, application_name):
    while True:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", f"{namespace}", "-l", f"run={application_name}", "-o", "yaml"],
            capture_output=True,
            text=True
        )
        pods = yaml.safe_load(result.stdout)
        running_pods = [pod for pod in pods["items"] if
                        pod["status"]["phase"] == "Running" or pod["status"]["phase"] == "Terminating"]
        if len(running_pods) == num_replicas:
            break
        log(f"Waiting for {len(running_pods)}/{num_replicas} application ({application_name}) pods to completely stop...")
        time.sleep(5)  # Wait for 10 seconds before checking again


# Function to delete the deployment and service
def clean_up():
    for app in kube_application_names:
        subprocess.run(["kubectl", "scale", "deployment", f"{app}", "-n", f"{namespace}", "--replicas=0"])


def get_formatted_time():
    # This format is expected by the data extractor
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time


def zip_snapshot(snapshot_path, yolo_csv_folder=None, name="yolov8n"):
    pass
    """
    import os
    import zipfile
    import shutil
    start_zip_time = time.time()
    # Copy yolo CSVs
    if yolo_csv_folder is not None:
        # Copy contents from yolo_csv_folder to snapshot_path
        destination_yolo_folder = os.path.join(snapshot_path, "yolo_outputs")
        shutil.copytree(yolo_csv_folder, destination_yolo_folder)
        log(f"Copied warehouse CSV files from {yolo_csv_folder} to {destination_yolo_folder}")
    # Copying the current script and its configurations to the snapshot
    current_script_path = __file__  # Path to the current script
    script_destination = os.path.join(snapshot_path, os.path.basename(current_script_path))
    shutil.copy2(current_script_path, script_destination)
    log(f"Copied current script to {script_destination}")
    # Extracting git commit and date
    result = subprocess.run(["git", "log", "-1", "--pretty=format:%H %ad"], capture_output=True, text=True)
    git_commit_info = result.stdout.strip()
    git_info_path = os.path.join(snapshot_path, "git_commit_info.txt")
    with open(git_info_path, "w") as git_info_file:
        git_info_file.write(git_commit_info)
    log(f"Copied git commit info to {git_info_path}")
    # Create a zip file from the snapshot_path
    zip_filename = f"{int(start_zip_time)}_{name}.zip"
    zip_filepath = os.path.join(os.path.dirname(snapshot_path), zip_filename)
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(snapshot_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, snapshot_path)
                zipf.write(file_path, arcname)
    end_zip_time = time.time()
    zip_duration = end_zip_time - start_zip_time
    zip_size = os.path.getsize(zip_filepath)
    # Optionally delete the original files
    delete_original = True  # Set this to False if you do not want to delete
    if delete_original:
        shutil.rmtree(snapshot_path)
        if yolo_csv_folder is not None:
            shutil.rmtree(yolo_csv_folder)
        log(f"Deleting original files in {snapshot_path} and {yolo_csv_folder}")
    # Log the details
    log(f"Zipping completed in {zip_duration:.2f} seconds")
    log(f"Zip file size: {zip_size / (1024 * 1024):.2f} MB")
    log(f"Zip file path: {zip_filepath}")
    """


log(f"Removing any leftover containers from previous experiments...")
clean_up()
wait_for_terminate(0, master_name)
wait_for_terminate(0, worker_name)


runs = [(workers, points) for workers in num_workers for points in lidar_points]
for run in runs:
    workers, points = run
    run_name = f"{run}"
    log(f"Starting experiment with workers={workers} and lidar_points={points}")
    master_csv_folder = f"qos_outputs/{time.time()}_{run_name}_master/"
    worker_csv_folder = f"qos_outputs/{time.time()}_{run_name}_worker/"
    master_qos_saver = MessageToCSVProcessor(master_csv_folder)
    worker_qos_saver = MessageToCSVProcessor(worker_csv_folder)

    # Init and/or reset kafka
    # Specify kafka topics and the number of partitions
    topics = {"grid_worker_input": workers, "grid_master_input": 1, "grid_worker_validate": 1, "grid_master_validate": 1}
    log(f"Make sure the Kafka topics exist")
    for topic, num_partitions in topics.items():
        # Make sure the topic is initialized with correct amount of partitions
        kafka_init.init_kafka(kafka_servers=kafka_servers, num_partitions=num_partitions, topic_name=topic)
        # Make sure the topic contains no messages from previous experiments
        kafka_init.clear_topic(kafka_servers=kafka_servers, topic_name=topic)

    # Update yaml and deploy
    log("")
    yaml_config = {"KAFKA_SERVERS": kafka_servers,
                   "VERBOSE": "FALSE",
                   "VISUALIZE": "VISUALIZE"}
    deploy_worker_experiment_path = os.path.join(os.path.dirname(worker_csv_folder), "worker.yaml")
    deploy_master_experiment_path = os.path.join(os.path.dirname(master_csv_folder), "master.yaml")

    # Update YAML (Workers)
    log(f"Creating a new deployment YAML with config {yaml_config} to {deploy_worker_experiment_path}")
    create_deployment_yaml.update_warehouse_model(deploy_worker_template_path, deploy_worker_experiment_path, yaml_config)
    # Update YAML (Master)
    log(f"Creating a new deployment YAML with config {yaml_config} to {deploy_master_experiment_path}")
    create_deployment_yaml.update_warehouse_model(deploy_master_template_path, deploy_master_experiment_path, yaml_config)

    # Deploy and scale applications
    subprocess.run(["kubectl", "apply", "-f", deploy_worker_experiment_path])
    scale_and_wait_for_replicas(application_name=worker_name, num_replicas=workers)
    subprocess.run(["kubectl", "apply", "-f", deploy_master_experiment_path])
    scale_and_wait_for_replicas(application_name=master_name, num_replicas=1)

    log("Application deployed.")
    log(f"Waiting for {idle_before_start_1} seconds so applications have a chance to set up completely")
    # Maybe related Kafka issue: https://github.com/akka/alpakka-kafka/issues/382
    # Our problem also seems to happen like: A) consumer pulls message B) other consumer connects C) Kafka reassigns -> message lost
    time.sleep(idle_before_start_1)  # Wait for initialization (How to know how long to wait?)
    # Check that the applications are ready
    log("")
    log("Sending some data to check that at least one pod can process data.")

    msgs_sent = feeder.run(num_items=5,
                           num_threads=workers,
                           kafka_servers=kafka_servers)
    msg_ids = set(x for x in range(msgs_sent))
    log("Waiting for results on the test image.")
    temp_validator = ValidationThread(kafka_servers=kafka_servers, kafka_topic="grid_master_validate")
    num_received = temp_validator.wait_for_msg_ids(msg_ids, timeout_s=600)

    if num_received != msgs_sent:
        log("Test timed out!")
        # TODO: How to handle this situation?
    else:
        log("Test successful.")


    # Start measuring the cluster from this point forwards
    start_time = get_formatted_time()
    log(start_time)
    log(f"Waiting for {idle_before_start_2} seconds")
    time.sleep(
        idle_before_start_2)  # Wait for slower consumers to start and to give some slack on the measurement data
    # Feed frames
    log("")
    log(f"Feeding data (frames: {None} frames -- num_workers: {None}).")

    master_validator = ValidationThread(kafka_servers=kafka_servers, kafka_topic="grid_master_validate",
                                        msg_callback=master_qos_saver.process_event)
    master_validator.start()
    worker_validator = ValidationThread(kafka_servers=kafka_servers, kafka_topic="grid_worker_validate",
                                        msg_callback=worker_qos_saver.process_event)
    worker_validator.start()

    frames_sent = feeder.run(num_items=1000, # TODO: how many items?
                             num_threads=workers,
                             kafka_servers=kafka_servers)
    msg_ids = set(x for x in range(frames_sent))
    log(f"Completed sending {frames_sent} point clouds.\n")
    # Wait for results
    log("Waiting for results.")

    num_received_1 = master_validator.wait_for_msg_ids(msg_ids, timeout_s=600)
    num_received_2 = worker_validator.wait_for_msg_ids(msg_ids, timeout_s=600)
    log(f"Sent {msgs_sent}, received {num_received_1} and {num_received_2} messages from master and worker respectively.")

    log(f"Waiting for {idle_after_end} seconds")
    time.sleep(idle_after_end)
    end_time = get_formatted_time()
    # Clean up the deployment (preferably start this process before data extractor to parallelize them)
    log("")
    log(f"Cleaning up...")
    clean_up()
    master_qos_saver.close()
    worker_qos_saver.close()

    log(end_time)
    log(f"Extracting data...")
    snapshot_results = extractor.create_snapshot(
        start_time=start_time,
        end_time=end_time,
        sampling=5,  # Sampling rate used by prometheus during the experiment (seconds)
        segment_size=1000,
        n_threads=4,  # Cluster nodes have 4 cores?
    )
    log("Data extracted.")
    log(snapshot_results)
    # Zip all experiment data and delete unzipped data
    log("Zipping all experiment data...")
    snapshot_path = snapshot_results["path"]
    """
    TODO: Implement zipping
    zip_snapshot(snapshot_path, yolo_csv_folder, name=f"{run_name}")
    """

    log(f"Zipping done\n")
    """
    TODO: Wait for delayed results (or just empty the msg queues?)
    log(f"Waiting for any delayed images before the next experiment...")
    leftover_images = dummy_validate.wait_for_results(image_ids, kafka_servers=kafka_servers, msg_callback=None,
                                                      timeout_s=10)
    log(f"Received {leftover_images} delayed images.")
    """

    log(f"Experiment with warehouse_MODEL={run_name} completed.\n\n")
log("All experiments completed.")
