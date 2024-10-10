import logging
import os
import subprocess
import time
import yaml
import create_deployment_yaml
from data_feeder import dummy_feeder, dummy_validate, yolo_to_csv
import deploy_experiment
from data_extractor import extractor
import datetime

# Define the different YOLO_MODEL values to test
yolo_models = ["yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x"]
yolo_models = ["yolov8n", "yolov8s"]#, "yolov8m", "yolov8l", "yolov8x"]
idle_before_start = 0.1*60 # (seconds) Wait for yolo instances to start
idle_after_end = 0.5*60 # (seconds) Catch the tail of the experiment metrics
yaml_template_path = "consumer_template.yaml"  # Template for running the experiments
yaml_experiment_path = None  # This file will be created from the template


# Function to deploy the application
def deploy_application(yolo_model):
    # deploy_experiment.deploy_application(yolo_model)
    subprocess.run(["kubectl", "apply", "-f", "ov_deployment.yaml"])

    replicas = 2
    subprocess.run(["kubectl", "scale", "deployment", "yolo-consumer", "-n", "workloadb", f"--replicas={replicas}"])

    # Wait until 5 instances of pod "yolo-consumer" from namespace "workloadb" are running
    while True:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "workloadb", "-l", "run=yolo-consumer", "-o", "yaml"],
            capture_output=True,
            text=True
        )
        pods = yaml.safe_load(result.stdout)
        running_pods = [pod for pod in pods["items"] if pod["status"]["phase"] == "Running"]
        if len(running_pods) >= replicas:
            break
        log(f"Waiting for {len(running_pods)}/{replicas} yolo-consumer pods to be running...")
        time.sleep(5)  # Wait for 10 seconds before checking again

# Function to delete the deployment and service
def clean_up():
    # deploy_experiment.clean_up()
    subprocess.run(["kubectl", "scale", "deployment", "yolo-consumer", "-n", "workloadb", "--replicas=0"])

def wait_for_yolo_outputs():
    pass

def collect_data():
    pass

logging.basicConfig(
    filename=f'{time.time()}_experiment.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

def log(message):
    logging.info(message)
    print(message)

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


for model in yolo_models:
    log(f"Starting experiment with YOLO_MODEL={model}")

    log("Starting to log yolo results to ")
    yolo_csv_folder = f"yolo_outputs/{time.time()}_{model}/"
    yolo_saver = yolo_to_csv.YoloToCSV(yolo_csv_folder)

    # Update yaml and deploy
    yaml_config = {"YOLO_MODEL": model}
    yaml_experiment_path = os.path.join(os.path.dirname(yolo_csv_folder), "consumer.yaml")
    log(f"Creating a new deployment YAML with config {yaml_config} to {yaml_experiment_path}")
    create_deployment_yaml.update_yolo_model(yaml_template_path, yaml_experiment_path, yaml_config)
    deploy_application(model)
    log("Application deployed.")

    # Check that the applications are ready
    log("Sending one image that at least one pod can process data.")
    images_sent = dummy_feeder.feed_data(1)
    image_ids = set(x for x in range(images_sent))
    log("Waiting for results on the test image.")
    num_received = dummy_validate.wait_for_results(image_ids, msg_callback=None, timeout_s=600)
    if num_received != images_sent:
        log("Test timed out!")
        # TODO: How to handle this situation?
    else:
        log("Test successful.")

    # Start measuring the cluster from this point forwards
    start_time = get_formatted_time()
    log(start_time)
    log(f"Waiting for {idle_before_start} seconds")
    time.sleep(idle_before_start)  # Wait for slower consumers to start and to give some slack on the measurement data

    # Feed images
    log("Feeding data.")
    images_sent = dummy_feeder.feed_data(1000)
    image_ids = set(x for x in range(images_sent))

    # Wait for results
    log("Waiting for results.")
    dummy_validate.wait_for_results(image_ids, msg_callback=yolo_saver.process_event)
    log(f"Waiting for {idle_after_end} seconds")
    time.sleep(idle_after_end)
    end_time = get_formatted_time()

    # Clean up the deployment (preferably start this process before data extractor to parallelize them)
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
    zip_snapshot(snapshot_path, yolo_csv_folder, name=model)

    log(f"Experiment with YOLO_MODEL={model} completed.\n\n")

log("All experiments completed.")
