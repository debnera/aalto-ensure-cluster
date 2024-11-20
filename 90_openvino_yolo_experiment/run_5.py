"""
Run_5: Test limits for all models

- All models and resolutions
- Send n images in the shortest amount of time possible

"""


import logging
import os
import socket
import subprocess
import time
import yaml
import create_deployment_yaml
from data_feeder import dummy_feeder, dummy_validate, yolo_to_csv, day_night_feeder, kafka_init, linear_feeder, burst_feeder
from data_extractor import extractor
import datetime
import argparse  # New import for argument parsing

# Argument parser for command-line arguments
parser = argparse.ArgumentParser(description="Run YOLO experiments with optional smoketest.")
parser.add_argument("--smoketest", action="store_true", help="Run a short smoketest.")

args = parser.parse_args()  # Parse arguments

# Define the different YOLO_MODEL values to test
yolo_models = []
yolo_models += ["yolo11n", "yolo11s", "yolo11m", "yolo11l", "yolo11x"]  # YOLO v11 released on v8.3.0 (2024-09-29)
yolo_models += ["yolov10n", "yolov10s", "yolov10m", "yolov10l", "yolov10x"]
yolo_models += ["yolov9t", "yolov9s", "yolov9m", "yolov9c", "yolov9e"]  # NOTE: Different naming on v9 yolo_models
yolo_models += ["yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x"]
# feeder = day_night_feeder
feeder = burst_feeder  # Use linear_feeder or day_night_feeder
resolutions = [160, 320, 640, 1280]
idle_before_start_1 = 120 # (seconds) Wait for yolo instances to receive their kafka assignments - otherwise might get stuck
idle_before_start_2 = 0.5 * 60  # (seconds) Additional wait after Kafka is verified working
idle_after_end = 0.5 * 60  # (seconds) Catch the tail of the experiment metrics
num_images_for_small_models = 5000  # (1000 img -> 2s to send --- 5000 img -> 10s to send)
num_images_for_large_models = 1000
large_models_end_with = ["m", "l", "x", "c", "e"]
yaml_template_path = "consumer_template.yaml"  # Template for running the experiments
yaml_experiment_path = None  # This file will be created from the template
# kafka_servers = 'localhost:10001,localhost:10002,localhost:10003'  # Servers for local testing
kafka_servers = "130.233.193.117:10001"  # Servers for running on our cluster
num_yolo_consumers = 5

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


    resolutions = [160]  # Only one resolution for smoketest
    yolo_models = ["yolo11n"]  # Only one model for smoketest
    experiment_duration = 60  # Short experiment duration
    idle_before_start_2 = 10  # Shorter wait times
    idle_after_end = 10


def wait_for_amount_replicas(num_replicas):
    while True:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "workloadb", "-l", "run=yolo-consumer", "-o", "yaml"],
            capture_output=True,
            text=True
        )
        pods = yaml.safe_load(result.stdout)
        running_pods = [pod for pod in pods["items"] if pod["status"]["phase"] == "Running"]
        if len(running_pods) == num_replicas:
            break
        log(f"Waiting for {len(running_pods)}/{num_replicas} yolo-consumer pods to be running...")
        time.sleep(5)  # Wait for 10 seconds before checking again


def wait_for_terminate(num_replicas):
    while True:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "workloadb", "-l", "run=yolo-consumer", "-o", "yaml"],
            capture_output=True,
            text=True
        )
        pods = yaml.safe_load(result.stdout)
        running_pods = [pod for pod in pods["items"] if
                        pod["status"]["phase"] == "Running" or pod["status"]["phase"] == "Terminating"]
        if len(running_pods) == num_replicas:
            break
        log(f"Waiting for {len(running_pods)}/{num_replicas} yolo-consumer pods to completely stop...")
        time.sleep(5)  # Wait for 10 seconds before checking again


# Function to delete the deployment and service
def clean_up():
    subprocess.run(["kubectl", "scale", "deployment", "yolo-consumer", "-n", "workloadb", "--replicas=0"])


def wait_for_yolo_outputs():
    pass


def collect_data():
    pass








def get_formatted_time():
    # This format is expected by the data extractor
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time


def zip_snapshot(snapshot_path, yolo_csv_folder=None, name="yolov8n"):
    import os
    import zipfile
    import shutil
    start_zip_time = time.time()
    # Copy yolo CSVs
    if yolo_csv_folder is not None:
        # Copy contents from yolo_csv_folder to snapshot_path
        destination_yolo_folder = os.path.join(snapshot_path, "yolo_outputs")
        shutil.copytree(yolo_csv_folder, destination_yolo_folder)
        log(f"Copied YOLO CSV files from {yolo_csv_folder} to {destination_yolo_folder}")
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


log(f"Removing any leftover containers from previous experiments...")
clean_up()
log(f"Make sure the Kafka topics exist")
kafka_init.init_kafka(kafka_servers=kafka_servers, num_partitions=num_yolo_consumers)
wait_for_terminate(0)
log(f"Waiting for any delayed images before the next experiment...")
leftover_images = dummy_validate.wait_for_results({-1}, kafka_servers=kafka_servers, msg_callback=None, timeout_s=5)
log(f"Received {leftover_images} delayed images.")

for resolution in resolutions:
    for model in yolo_models:
        run_name = f"{model}_{resolution}"
        log(f"Starting experiment with YOLO_MODEL={run_name}")
        log("Starting to log yolo results to ")
        yolo_csv_folder = f"yolo_outputs/{time.time()}_{run_name}/"
        yolo_saver = yolo_to_csv.YoloToCSV(yolo_csv_folder)
        # Update yaml and deploy
        log("")
        yaml_config = {"YOLO_MODEL": model,
                       "KAFKA_SERVERS": kafka_servers,
                       "RESOLUTION": str(resolution),
                       "VERBOSE": "FALSE"}
        yaml_experiment_path = os.path.join(os.path.dirname(yolo_csv_folder), "consumer.yaml")
        log(f"Creating a new deployment YAML with config {yaml_config} to {yaml_experiment_path}")
        create_deployment_yaml.update_yolo_model(yaml_template_path, yaml_experiment_path, yaml_config)
        subprocess.run(["kubectl", "apply", "-f", yaml_experiment_path])
        subprocess.run(
            ["kubectl", "scale", "deployment", "yolo-consumer", "-n", "workloadb", f"--replicas={num_yolo_consumers}"])
        wait_for_amount_replicas(num_yolo_consumers)
        log("Application deployed.")
        log(f"Waiting for {idle_before_start_1} seconds so applications have a chance to set up completely")
        # Maybe related Kafka issue: https://github.com/akka/alpakka-kafka/issues/382
        # Our problem also seems to happen like: A) consumer pulls message B) other consumer connects C) Kafka reassigns -> message lost
        time.sleep(idle_before_start_1)  # Wait for initialization (How to know how long to wait?)
        # Check that the applications are ready
        log("")
        log("Sending some images to check that at least one pod can process data.")
        images_sent = dummy_feeder.feed_data(5, kafka_servers=kafka_servers)
        image_ids = set(x for x in range(images_sent))
        log("Waiting for results on the test image.")
        num_received = dummy_validate.wait_for_results(image_ids, kafka_servers=kafka_servers, msg_callback=None,
                                                       timeout_s=600)
        if num_received != images_sent:
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
        # Feed images
        log("")
        is_large_model = False
        for letter in large_models_end_with:
            if model.endswith(letter):
                is_large_model = True
        print(f"Model {model} is_large_model={is_large_model}")
        if is_large_model:
            num_images = num_images_for_large_models
        else:
            num_images = num_images_for_small_models
        log(f"Feeding data (target: {num_images} images).")
        images_sent = feeder.run(num_images,
                                 kafka_servers=kafka_servers)
        image_ids = set(x for x in range(images_sent))
        log(f"Completed sending {images_sent} images.\n")
        # Wait for results
        log("Waiting for results.")
        num_received = dummy_validate.wait_for_results(image_ids, kafka_servers=kafka_servers,
                                                       msg_callback=yolo_saver.process_event)
        log(f"Sent {images_sent}, received {num_received} images.")
        log(f"Waiting for {idle_after_end} seconds")
        time.sleep(idle_after_end)
        end_time = get_formatted_time()
        # Clean up the deployment (preferably start this process before data extractor to parallelize them)
        log("")
        log(f"Cleaning up...")
        clean_up()
        yolo_saver.save_to_csv()

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
        zip_snapshot(snapshot_path, yolo_csv_folder, name=f"{run_name}")
        log(f"Zipping done\n")
        log(f"Waiting for any delayed images before the next experiment...")
        leftover_images = dummy_validate.wait_for_results(image_ids, kafka_servers=kafka_servers, msg_callback=None,
                                                          timeout_s=10)
        log(f"Received {leftover_images} delayed images.")
        log(f"Experiment with YOLO_MODEL={run_name} completed.\n\n")
log("All experiments completed.")
