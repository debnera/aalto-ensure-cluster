import numpy as np

from .utilz.dataset_utils import load_dataset
from .utilz.misc import resource_exists, log, create_lock, resize_array
from .utilz.kafka_utils import create_producer
from threading import Thread, Semaphore
import time, math, random, argparse
import itertools


"""
Burst feeder: Send specified number of images as fast as possible.
"""

# python3 feeder.py --num_images 100

# PARSE PYTHON ARGUMENTS
parser = argparse.ArgumentParser()
parser.add_argument(
    "-n",
    "--num_images",
    type=int,
    default=1,
    help="Number of images to send. Default: 100."
)
parser.add_argument(
    "-t",
    "--num_threads",
    type=int,
    default=4,
    help="Number of threads to use. Default: 4."
)

def run(num_images=100, num_threads=4, kafka_servers="130.233.193.117:10001", dataset_path="./data_feeder/datasets/mini.hdf5"):


    image_count = itertools.count()
    # DYNAMIC ARGUMENTS
    dataset_args = {
        'dataset': {
            'dataset_path': dataset_path,
            'name': 'mini',
            'max_frames': -1,
            'max_vehicles': -1,
            'fps': 5,
            'repeat': 1,
        },
    }

    ########################################################################################
    ########################################################################################

    # MAKE SURE THE HDF5 DATASET EXISTS
    if not resource_exists(f'{dataset_path}'):
        return next(image_count)

    # INSTANTIATE THREAD KILL SIGNAL
    alive_lock = create_lock()

    # KEEP TRACK THREADS AND KAFKA PRODUCERS
    threads = []
    kafka_producers = []

    # CREATE KAFKA PRODUCERS FOR EACH THREAD
    for _ in range(num_threads):
        kafka_producer = create_producer(kafka_servers=kafka_servers)
        kafka_producers.append(kafka_producer)

    # MAKE SURE KAFKA CONNECTION IS OK
    for i, producer in enumerate(kafka_producers):
        if not producer.connected():
            log(f'KAFKA PRODUCER NUMBER {i} NOT CONNECTED! ABORTING...')
            return next(image_count)

    # LOAD THE DATASET
    dataset = load_dataset(dataset_args['dataset'])
    dataset_length = len(dataset)
    avg_dataset_item_size = math.ceil(sum([len(x) for x in dataset]) / len(dataset))

    ########################################################################################
    ########################################################################################

    # PRODUCER THREAD WORK LOOP
    def thread_work(nth_thread, alive_signal, images_to_send):
        # RANDOMLY PICK A STARTING INDEX FROM THE DATASET
        next_index = random.randrange(dataset_length)

        time_until_start = experiment_start - time.time()
        log(f'THREAD {nth_thread} WILL SEND {images_to_send} IMAGES AFTER {time_until_start} SECONDS')

        # BUSY WAIT FOR A BIT TO SYNC THREADS
        while time.time() < experiment_start:
            pass

        # SEND SPECIFIED AMOUNT OF IMAGES
        for image in range(images_to_send):
            if not alive_signal.is_active():
                log(f'THREAD {nth_thread} WAS KILLED AT {time.time()}')
                return
            image = dataset[next_index]
            img_as_bytes = image
            image_id = next(image_count)
            image_id_encoded = str(image_id).encode('utf-8')
            kafka_producers[nth_thread - 1].push_msg('yolo_input', img_as_bytes, key=image_id_encoded)

            # INCREMENT ROLLING INDEX
            next_index = (next_index+1) % dataset_length

        ended = time.time()
        log(f'THREAD {nth_thread} HAS FINISHED AT {ended} -- (took {ended - experiment_start}) s')

    ########################################################################################
    ########################################################################################

    try:
        experiment_start = time.time() + 3

        log(f'CREATING PRODUCER THREAD POOL ({num_threads})')

        images_per_thread = math.ceil(num_images / num_threads)
        for nth in range(num_threads):
            thread = Thread(target=thread_work, args=(nth+1, alive_lock, images_per_thread))
            threads.append(thread)
            thread.start()

        # WAIT FOR EVERY THREAD TO FINISH (MUST BE MANUALLY KILLED BY CANCELING LOCK)
        [[thread.join() for thread in threads]]
        end_time = time.time()
        duration = end_time - experiment_start
        bps = (avg_dataset_item_size * num_images) / duration
        mbps = bps / 1000000  # Bytes or bits...? Assuming bytes, since each image is in byte-format
        log(f'EXPERIMENT DONE')
        log(f'SENT {num_images} IMAGES IN {duration} SECONDS ({mbps} MB/s)')

    # TERMINATE MAIN PROCESS AND KILL HELPER THREADS
    except KeyboardInterrupt:
        alive_lock.kill()
        log('WORKER & THREADS MANUALLY KILLED..', True)

    return next(image_count)

if __name__ == '__main__':
    py_args = parser.parse_args()
    run(py_args.num_images, py_args.num_threads)
