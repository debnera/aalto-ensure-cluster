import subprocess
import time
import yaml
from data_feeder import dummy_feeder, dummy_validate
import deploy_experiment
import data_extractor
import datetime

# Define the different YOLO_MODEL values to test
yolo_models = ["yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x"]


# Function to deploy the application
def deploy_application(yolo_model):
    # deploy_experiment.deploy_application(yolo_model)
    subprocess.run(["kubectl", "apply", "-f", "ov_deployment.yaml"])

    # # Wait until 5 instances of pod "yolo-consumer" from namespace "workloadb" are running
    # while True:
    #     result = subprocess.run(
    #         ["kubectl", "get", "pods", "-n", "workloadb", "-l", "app=yolo-consumer", "-o", "yaml"],
    #         capture_output=True,
    #         text=True
    #     )
    #     pods = yaml.safe_load(result.stdout)
    #     running_pods = [pod for pod in pods["items"] if pod["status"]["phase"] == "Running"]
    #     if len(running_pods) >= 5:
    #         break
    #     print("Waiting for 5 yolo-consumer pods to be running...")
    #     time.sleep(10)  # Wait for 10 seconds before checking again

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

    start_time = get_formatted_time()
    print(start_time)

    # Feed images
    print("Feeding data.")
    images_sent = dummy_feeder.feed_data(10)
    image_ids = set(x for x in range(images_sent))

    # Wait for results
    print("Waiting for results.")
    dummy_validate.wait_for_results(image_ids)

    # Clean up the deployment
    clean_up()
    
    collect_data()
    end_time = get_formatted_time()
    print(end_time)
    # data_extractor.create_snapshot(
    #     start_time=start_time,
    #     end_time=end_time,
    #     sampling=5,  # Sampling rate used by prometheus during the experiment (seconds)
    #     segment_size=1000,
    #     n_threads=4,  # Cluster nodes have 4 cores?
    # )

    print(f"Experiment with YOLO_MODEL={model} completed.\n\n")

print("All experiments completed.")
