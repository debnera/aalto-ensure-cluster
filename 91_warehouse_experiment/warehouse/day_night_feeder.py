import argparse
import itertools
import math
import time
import numpy as np
from threading import Thread

from .utils.kafka_utils import create_producer
from .utils.lidar_dataset_reader import load_to_memory
from .utils.misc import resource_exists, log, create_lock

"""
Burst feeder: Send specified number of sensor data as fast as possible.
"""

# python3 feeder.py --num_items 100

# Parse Python arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "-m",
    "--max_mbps",
    type=int,
    default=1,
    help="Feeder tries to keep this amount of MB/s. Default: 1.",
)
parser.add_argument(
    "-d",
    "--duration",
    type=int,
    default=600,
    help="The experiment duration in seconds. Default: 10 minutes.",
)
parser.add_argument(
    "-t",
    "--num_threads",
    type=int,
    default=4,
    help="Number of threads to use. Default: 4."
)

def compute_feeding_scale(time_elapsed_seconds, max_duration_seconds, n_cycles):
    """  """
    default_cycle = [
        0.03, 0.06, 0.09, 0.12, 0.266, 0.412,
        0.558, 0.704, 0.85, 0.7625, 0.675, 0.587,
        0.5, 0.59, 0.68, 0.77, 0.86, 0.97,
        0.813, 0.656, 0.5, 0.343, 0.186, 0.03
    ] * n_cycles

    # The corresponding time points for the 24 original values
    original_time_points = np.linspace(0, max_duration_seconds, len(default_cycle))

    # Perform linear interpolation for the arbitrary time
    interpolated_value = np.interp(time_elapsed_seconds, original_time_points, default_cycle)
    return interpolated_value


def run(target_mbps=1, breakpoints=200, n_cycles=5, num_threads=4, duration_seconds=600,
        # kafka_servers="130.233.193.117:10001",
        kafka_servers="localhost:10001",
        dataset_path="../robots-4/points-per-frame-5000.hdf5"):
    msg_count = itertools.count()

    # Ensure the HDF5 dataset exists
    if not resource_exists(f'{dataset_path}'):
        return next(msg_count)

    # Instantiate the thread kill signal
    alive_lock = create_lock()

    # Keep track of threads and Kafka producers
    threads = []
    kafka_producers = []

    # Create Kafka producers for each thread
    for _ in range(num_threads):
        kafka_producer = create_producer(kafka_servers=kafka_servers)
        kafka_producers.append(kafka_producer)

    # Verify Kafka connections
    for i, producer in enumerate(kafka_producers):
        if not producer.connected():
            log(f'KAFKA PRODUCER NUMBER {i} NOT CONNECTED! ABORTING...')
            return next(msg_count)

    # Load the dataset
    all_sensor_data = load_to_memory(dataset_path)
    num_sensors = len(all_sensor_data)
    example_frame = all_sensor_data[0][0]
    elements_per_frame = example_frame.data.size
    bytes_per_frame = example_frame.data.nbytes
    events_per_second = (target_mbps * 1024 * 1024) / bytes_per_frame
    original_time_between_events = (1 / (events_per_second / num_threads))
    total_items = duration_seconds * events_per_second
    items_per_thread = math.ceil(total_items / num_threads)

    # Thread work loop
    def thread_work(nth_thread, alive_signal, items_to_send):
        sensor_index = nth_thread % num_sensors
        sensor_frames = all_sensor_data[sensor_index]
        index = 0
        experiment_end = experiment_start + duration_seconds
        time_until_start = experiment_start - time.time()
        log(f'THREAD {nth_thread} WILL SEND ITEMS FOLLOWING THE DAY-NIGHT-CYCLE FROM SENSOR {sensor_index} AFTER {time_until_start} SECONDS')

        while time.time() < experiment_start:
            pass

        while time.time() < experiment_end:
            seconds_elapsed = time.time() - experiment_start
            current_scale = compute_feeding_scale(seconds_elapsed, duration_seconds, n_cycles)
            time_between_events = original_time_between_events * current_scale

            start_time = time.time()
            if not alive_signal.is_active():
                log(f'THREAD {nth_thread} WAS KILLED AT {time.time()}')
                return
            frame = sensor_frames[index % len(sensor_frames)]
            data_as_bytes = frame.to_bytes()
            item_id = next(msg_count)
            item_id_encoded = str(item_id).encode('utf-8')
            kafka_producers[nth_thread - 1].push_msg('grid_worker_input', data_as_bytes, key=item_id_encoded)
            index += 1
            end_time = time.time()
            remaining_wait_time = time_between_events - (end_time - start_time)
            if remaining_wait_time > 0:
                # Time.sleep is not an exact way to accomplish this, but our goal is to guarantee max_mbps, not min_mbps
                time.sleep(remaining_wait_time)

        ended = time.time()
        log(f'THREAD {nth_thread} HAS FINISHED AT {ended} -- (took {ended - experiment_start}) s')

    try:
        experiment_start = time.time() + 3

        log(f'CREATING PRODUCER THREAD POOL ({num_threads})')

        for nth in range(num_threads):
            thread = Thread(target=thread_work, args=(nth + 1, alive_lock, items_per_thread))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        [[thread.join() for thread in threads]]
        end_time = time.time()
        duration = end_time - experiment_start
        bps = (bytes_per_frame * total_items) / duration
        mbps = bps / (1024 * 1024)  # Conversion from bytes to megabytes
        log(f'EXPERIMENT DONE')
        log(f'SENT ~{total_items} ITEMS IN {duration} SECONDS ({mbps} MB/s)')

    except KeyboardInterrupt:
        alive_lock.kill()
        log('WORKER & THREADS MANUALLY KILLED..', True)

    return next(msg_count)


if __name__ == '__main__':
    py_args = parser.parse_args()
    run(py_args.num_items, py_args.num_threads)
