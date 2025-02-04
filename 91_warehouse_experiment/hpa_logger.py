import subprocess
import csv
import time
from datetime import datetime

# File path for storing the CSV data
OUTPUT_FILE = "hpa_status_log.csv"


# Function to get HPA metrics
def get_hpa_metrics(hpa_name, namespace):
    try:
        # Run kubectl command to get HPA details
        result = subprocess.run(
            ["kubectl", "get", "hpa", hpa_name, "-n", namespace, "-o", "json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        # Parse the JSON response (assuming kubectl is returning valid JSON)
        import json
        hpa_data = json.loads(result.stdout)

        # Extract metrics for CPU utilization and replicas
        current_cpu = hpa_data["status"]["currentMetrics"][0]["resource"]["current"]["averageUtilization"]
        replicas = hpa_data["status"]["currentReplicas"]

        return current_cpu, replicas

    except subprocess.CalledProcessError as e:
        print(f"Error fetching HPA metrics: {e.stderr}")
        return None, None
    except KeyError:
        # In case metrics are not available yet
        print(f"Metrics not available for HPA {hpa_name}")
        return None, None


def write_to_csv(timestamp, worker_cpu, master_cpu, worker_replicas, master_replicas):
    # Write data to CSV
    with open(OUTPUT_FILE, mode="a", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([timestamp, worker_cpu, master_cpu, worker_replicas, master_replicas])


if __name__ == "__main__":
    # CSV Header
    with open(OUTPUT_FILE, mode="w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["timestamp", "cpu-avg-worker", "cpu-avg-master", "replicas-worker", "replicas-master"])

    print("Starting to log HPA metrics every 5 seconds... Press Ctrl+C to stop.")
    try:
        while True:
            # Get timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                # Get `lidar-worker-hpa` metrics
                worker_cpu, worker_replicas = get_hpa_metrics("lidar-worker-hpa", "workloadc")

                # Get `lidar-master-hpa` metrics
                master_cpu, master_replicas = get_hpa_metrics("lidar-master-hpa", "workloadc")

                # Print status
                print(
                    f"[{timestamp}] "
                    f"cpu-avg-worker: {worker_cpu}, replicas-worker: {worker_replicas}, "
                    f"cpu-avg-master: {master_cpu}, replicas-master: {master_replicas}"
                )

                # Write results to CSV if metrics are available
                write_to_csv(timestamp, worker_cpu, master_cpu, worker_replicas, master_replicas)
            except:
                print(
                    f"[{timestamp}] no status available."
                )
                pass
            # Wait for 5 seconds
            time.sleep(5)

    except KeyboardInterrupt:
        print("Logging stopped.")
