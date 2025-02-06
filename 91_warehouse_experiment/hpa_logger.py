import csv
import subprocess
import threading
import time
import os
from datetime import datetime


class HPALogger:
    def __init__(self, output_file):
        self.output_file = output_file
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        self._stop_event = threading.Event()
        self._thread = None

    # File path for storing the CSV data
    def get_hpa_metrics(self, hpa_name, namespace):
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
            print(f"[HPA_LOGGER]: Error fetching HPA metrics: {e.stderr}")
            return None, None
        except KeyError:
            # In case metrics are not available yet
            print(f"[HPA_LOGGER]: Metrics not available for HPA {hpa_name}")
            return None, None

    def write_to_csv(self, timestamp, worker_cpu, master_cpu, worker_replicas, master_replicas):
        # Write data to CSV
        with open(self.output_file, mode="a", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow([timestamp, worker_cpu, master_cpu, worker_replicas, master_replicas])

    def _log_hpa_metrics(self):
        # CSV Header
        with open(self.output_file, mode="w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["timestamp", "cpu-avg-worker", "cpu-avg-master", "replicas-worker", "replicas-master"])

        print(f"[HPA_LOGGER]: Starting to log HPA metrics every 5 seconds... Press Ctrl+C to stop.")
        while not self._stop_event.is_set():
            # Get timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                # Get `lidar-worker-hpa` metrics
                worker_cpu, worker_replicas = self.get_hpa_metrics("lidar-worker-hpa", "workloadc")

                # Get `lidar-master-hpa` metrics
                master_cpu, master_replicas = self.get_hpa_metrics("lidar-master-hpa", "workloadc")

                # Print status
                print(
                    f"[{timestamp}] "
                    "[HPA_LOGGER]: "
                    f"cpu-avg-worker: {worker_cpu}, replicas-worker: {worker_replicas}, "
                    f"cpu-avg-master: {master_cpu}, replicas-master: {master_replicas}"
                )

                # Write results to CSV if metrics are available
                self.write_to_csv(timestamp, worker_cpu, master_cpu, worker_replicas, master_replicas)
            except:
                print(f"[{timestamp}] [HPA_LOGGER]:  no status available.")
                pass
            # Wait for 5 seconds
            time.sleep(5)

    def start_thread(self):
        if not self._thread or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._log_hpa_metrics, daemon=True)
            self._thread.start()
        else:
            print(f"[HPA_LOGGER]: Logger is already running.")

    def stop_thread(self):
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join()
            print(f"[HPA_LOGGER]: Logger stopped.")
        else:
            print(f"[HPA_LOGGER]: Logger is not running.")

if __name__ == "__main__":
    hpa_logger = HPALogger("hpa_metrics.csv")
    hpa_logger.start_thread()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        hpa_logger.stop_thread()

