import argparse
import itertools
import math
import time
import numpy as np
from threading import Thread
from typing import List

from .utils.kafka_utils import create_producer
from .utils.lidar_dataset_reader import load_to_memory
from .utils.misc import resource_exists, log, create_lock

"""
Day-night Feeder: Streams sensor data at a controlled rate over a specified duration using parallel threads.
"""

# Initialize argument parser to get runtime configuration
parser = argparse.ArgumentParser()
parser.add_argument(
    "-m", "--max_mbps",
    type=int,
    default=1,
    help="Target throughput in MB/s (default: 1 MB/s)."
)
parser.add_argument(
    "-d", "--duration",
    type=int,
    default=600,
    help="Experiment duration in seconds (default: 10 minutes)."
)
parser.add_argument(
    "-t", "--num_threads",
    type=int,
    default=4,
    help="Number of threads to use for data transmission (default: 4)."
)


def compute_feeding_scale(time_elapsed_seconds: float, max_duration_seconds: int, n_cycles: int) -> float:
    """
    Computes a scaling factor for data transmission rate based on the elapsed time.
    This simulates a day-night cycle using a sinusoidal-patterned interpolation.

    Args:
        time_elapsed_seconds (float): How far into the experiment we are, in seconds.
        max_duration_seconds (int): Total experiment duration in seconds.
        n_cycles (int): Number of day-night cycles within the experiment duration.

    Returns:
        float: Scaling factor to control transmission speed.
    """
    default_cycle = [
                        0.03, 0.06, 0.09, 0.12, 0.266, 0.412,
                        0.558, 0.704, 0.85, 0.7625, 0.675, 0.587,
                        0.5, 0.59, 0.68, 0.77, 0.86, 0.97,
                        0.813, 0.656, 0.5, 0.343, 0.186, 0.03
                    ] * n_cycles

    # Interpolate to find the scale value for the elapsed time
    original_time_points = np.linspace(0, max_duration_seconds, len(default_cycle))
    return float(np.interp(time_elapsed_seconds, original_time_points, default_cycle))


def run(
        msg_id_offset: int = 0,
        target_mbps: int = 1,
        n_cycles: int = 5,
        num_threads: int = 4,
        duration_seconds: int = 600,
        kafka_servers: str = "localhost:10001",
        dataset_path: str = "../robots-4/points-per-frame-5000.hdf5"
) -> int:
    """
    Runs the burst feeder experiment, streaming data to Kafka topics using multiple threads.

    Args:
        target_mbps (int): Target data rate in MB/s.
        n_cycles (int): Number of day-night cycles during the experiment.
        num_threads (int): Number of threads for parallel data transmission.
        duration_seconds (int): Experiment duration in seconds.
        kafka_servers (str): Kafka server connection string.
        dataset_path (str): Path to the HDF5 dataset to stream.

    Returns:
        int: Number of messages sent (used primarily for tracking/debugging).
    """
    # Generate unique IDs for each message
    msg_count = itertools.count()

    # Ensure the HDF5 dataset exists
    if not resource_exists(dataset_path):
        log(f"Dataset not found at {dataset_path}. Aborting.")
        return next(msg_count)

    # Create a lock for thread control
    alive_lock = create_lock()

    # List to track threads and Kafka producers
    threads = []
    kafka_producers = []

    # Initialize Kafka producers for each thread
    for _ in range(num_threads):
        kafka_producer = create_producer(kafka_servers=kafka_servers)
        kafka_producers.append(kafka_producer)

    # Verify all Kafka connections are active
    for i, producer in enumerate(kafka_producers):
        if not producer.connected():
            log(f"Kafka producer #{i} not connected. Aborting.")
            return next(msg_count)

    # Load the dataset into memory
    all_sensor_data = load_to_memory(dataset_path)
    num_sensors = len(all_sensor_data)
    example_frame = all_sensor_data[0][0]

    # Calculate frame and event properties
    bytes_per_frame = example_frame.data.nbytes
    events_per_second = (target_mbps * 1024 * 1024) / bytes_per_frame
    time_between_events = 1 / (events_per_second / num_threads)
    # total_items = duration_seconds * events_per_second
    # items_per_thread = math.ceil(total_items / num_threads)

    # Thread worker function
    def thread_work(nth_thread: int, alive_signal: create_lock) -> None:
        """
        Sends data frames from a specific thread to Kafka, adhering to the day-night cycle scaling.

        Args:
            nth_thread (int): Index of the current thread.
            alive_signal (create_lock): Signal to manage thread lifecycle.
            items_to_send (int): Number of items the thread is responsible for sending.
        """
        sensor_index = nth_thread % num_sensors
        sensor_frames = all_sensor_data[sensor_index]
        index = 0
        experiment_end = experiment_start + duration_seconds

        # Log thread start details
        log(f"Thread {nth_thread} sending data from sensor {sensor_index}.")

        # Wait for experiment start
        while time.time() < experiment_start:
            pass

        # Main transmission loop
        while time.time() < experiment_end:
            if not alive_signal.is_active():
                log(f"Thread {nth_thread} terminated.")
                return

            seconds_since_start = time.time() - experiment_start
            current_scale = compute_feeding_scale(seconds_since_start, duration_seconds, n_cycles)
            adjusted_time_between_events = time_between_events / current_scale  # Scale down msg throughput by increasing wait time

            start_time = time.time()  # Record start time of the event transmission

            # Send the frame and increment indices
            frame = sensor_frames[index % len(sensor_frames)]
            kafka_producers[nth_thread - 1].push_msg(
                'grid_worker_input',
                frame.to_bytes(),
                key=str(next(msg_count) + msg_id_offset).encode('utf-8')
            )
            index += 1

            # Calculate and respect the adjusted wait time before sending the next frame
            elapsed_time = time.time() - start_time
            remaining_time = adjusted_time_between_events - elapsed_time
            if remaining_time > 0:
                time.sleep(remaining_time)

        log(f"Thread {nth_thread} completed.")

    try:
        # Start the experiment after a short delay
        experiment_start = time.time() + 3
        log(f"Starting {num_threads} producer threads.")

        # Launch threads
        for nth in range(num_threads):
            thread = Thread(target=thread_work, args=(nth + 1, alive_lock))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        # Log experiment summary
        duration = time.time() - experiment_start

        # Peek msg_count without changing it
        total_items = next(msg_count)
        msg_count = itertools.count(start=total_items)

        total_bytes_sent = bytes_per_frame * total_items
        total_mb_sent = total_bytes_sent / (1024 * 1024)
        actual_mbps = total_mb_sent / duration
        log(f"Experiment completed. {total_items} items sent in {duration:.2f} seconds (~{actual_mbps:.2f} MB/s).")

    except KeyboardInterrupt:
        # Handle manual termination
        alive_lock.kill()
        log("Experiment terminated by user.")

    return next(msg_count)


if __name__ == "__main__":
    # Parse arguments and start the feeder
    py_args = parser.parse_args()
    run(
        target_mbps=py_args.max_mbps,
        num_threads=py_args.num_threads,
        duration_seconds=py_args.duration
    )
