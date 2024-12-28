import argparse
import itertools
import math
import time
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
    "-n",
    "--num_items",
    type=int,
    default=1000,
    help="Number of sensor data items to send. Default: 100."
)
parser.add_argument(
    "-t",
    "--num_threads",
    type=int,
    default=4,
    help="Number of threads to use. Default: 4."
)


def run(num_items=100, num_threads=4,
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

    # Thread work loop
    def thread_work(nth_thread, alive_signal, items_to_send):
        sensor_index = nth_thread % num_sensors
        sensor_frames = all_sensor_data[sensor_index]
        index = 0
        time_until_start = experiment_start - time.time()
        log(f'THREAD {nth_thread} WILL SEND {items_to_send} ITEMS FROM SENSOR {sensor_index} AFTER {time_until_start} SECONDS')

        while time.time() < experiment_start:
            pass

        for item in range(items_to_send):
            if not alive_signal.is_active():
                log(f'THREAD {nth_thread} WAS KILLED AT {time.time()}')
                return
            frame = sensor_frames[index % len(sensor_frames)]
            data_as_bytes = frame.to_bytes()
            item_id = next(msg_count)
            item_id_encoded = str(item_id).encode('utf-8')
            kafka_producers[nth_thread - 1].push_msg('grid_worker_input', data_as_bytes, key=item_id_encoded)
            index += 1

        ended = time.time()
        log(f'THREAD {nth_thread} HAS FINISHED AT {ended} -- (took {ended - experiment_start}) s')

    try:
        experiment_start = time.time() + 3

        log(f'CREATING PRODUCER THREAD POOL ({num_threads})')

        items_per_thread = math.ceil(num_items / num_threads)
        for nth in range(num_threads):
            thread = Thread(target=thread_work, args=(nth + 1, alive_lock, items_per_thread))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        [[thread.join() for thread in threads]]
        end_time = time.time()
        duration = end_time - experiment_start
        bps = (bytes_per_frame * num_items) / duration
        mbps = bps / (1024 * 1024)  # Conversion from bytes to megabytes
        log(f'EXPERIMENT DONE')
        log(f'SENT {num_items} ITEMS IN {duration} SECONDS ({mbps} MB/s)')

    except KeyboardInterrupt:
        alive_lock.kill()
        log('WORKER & THREADS MANUALLY KILLED..', True)

    return next(msg_count)


if __name__ == '__main__':
    py_args = parser.parse_args()
    run(py_args.num_items, py_args.num_threads)
