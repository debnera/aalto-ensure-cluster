import subprocess
import time
import yaml
from data_feeder import dummy_feeder, dummy_validate
import deploy_experiment
import data_extractor
import datetime

# Define the different YOLO_MODEL values to test
yolo_models = ["yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x"]
idle_before_start = 0.1*60 # (seconds) Wait for yolo instances to start
idle_after_end = 0.1*60 # (seconds) Catch the tail of the experiment metrics


# Function to deploy the application
def deploy_application(yolo_model):
    # deploy_experiment.deploy_application(yolo_model)
    subprocess.run(["kubectl", "apply", "-f", "ov_deployment.yaml"])
    replicas = 2

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
        print(f"Waiting for {len(running_pods)}/{replicas} yolo-consumer pods to be running...")
        time.sleep(5)  # Wait for 10 seconds before checking again
    print("Pods are up!")

# Function to delete the deployment and service
def clean_up():
    # deploy_experiment.clean_up()
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

for model in yolo_models:
    print(f"Starting experiment with YOLO_MODEL={model}")
    deploy_application(model)
    print("Application deployed.")
    print(f"Waiting for {idle_before_start} seconds")
    time.sleep(idle_before_start)

    start_time = get_formatted_time()
    print(start_time)

    # Feed images
    print("Feeding data.")
    images_sent = dummy_feeder.feed_data(100)
    image_ids = set(x for x in range(images_sent))

    # Wait for results
    print("Waiting for results.")
    dummy_validate.wait_for_results(image_ids)
    print(f"Waiting for {idle_after_end} seconds")
    time.sleep(idle_after_end)
    end_time = get_formatted_time()

    # Clean up the deployment (preferably start this process before data extractor to parallelize them)
    print(f"Cleaning up...")
    clean_up()


    print(end_time)
    print(f"Extracting data...")
    # data_extractor.create_snapshot(
    #     start_time=start_time,
    #     end_time=end_time,
    #     sampling=5,  # Sampling rate used by prometheus during the experiment (seconds)
    #     segment_size=1000,
    #     n_threads=4,  # Cluster nodes have 4 cores?
    # )

    print(f"Experiment with YOLO_MODEL={model} completed.\n\n")

print("All experiments completed.")
