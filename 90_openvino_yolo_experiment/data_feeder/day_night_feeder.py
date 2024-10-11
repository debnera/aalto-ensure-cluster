import cv2
import numpy as np

from .utilz.dataset_utils import load_dataset
from .utilz.misc import resource_exists, log, create_lock, resize_array
from .utilz.kafka_utils import create_producer
from threading import Thread, Semaphore
import time, math, random, argparse
import itertools

# python3 feeder.py --duration 7200 --breakpoints 200 --max_mbps 15

# PARSE PYTHON ARGUMENTS
parser = argparse.ArgumentParser()
parser.add_argument(
    "-m",
    "--max_mbps",
    type=int,
    default=1,
    help="MB/s limit at 100% throughput",
)
parser.add_argument(
    "-b",
    "--breakpoints",
    type=int,
    default=200,
    help="How many sections the experiment duration will be split into.",
)
parser.add_argument(
    "-d",
    "--duration",
    type=int,
    default=(60*60*2),
    help="The experiment duration in seconds",
)
parser.add_argument(
    "-c",
    "--n_cycles",
    type=int,
    default=5,
    help="How many day-night cycles should be performed",
)
parser.add_argument(
    "--compress",
    type=bool,
    default=False,
    help="Reduce amount of data sent through Kafka by compressing images to JPEG. The max throughput mbps is computed"
         "before this compression, and compression will not affect it.",
)

def run(max_mbps=1, breakpoints=200, duration_seconds=60 * 60 * 2, n_cycles=5, kafka_servers="130.233.193.117:10001", dataset_path="./data_feeder/datasets/mini.hdf5"):


    image_count = itertools.count()
    # DYNAMIC ARGUMENTS
    args = {
        'dataset': {
            'dataset_path': dataset_path,
            'name': 'mini',
            'max_frames': -1,
            'max_vehicles': -1,
            'fps': 5,
            'repeat': 1,
        },
        'num_threads': 4,

        # EXPERIMENT DETAILS
        'experiment': {
            'max_mbs': max_mbps,
            'n_breakpoints': breakpoints,
            'duration': duration_seconds,
        }
    }

    ########################################################################################
    ########################################################################################

    # MAKE SURE THE HDF5 DATASET EXISTS
    if not resource_exists(f'{dataset_path}'):
        return next(image_count)
    
    # INSTANTIATE THREAD LOCKS
    thread_lock = create_lock()
    semaphore = Semaphore(1)

    # KEEP TRACK THREADS AND KAFKA PRODUCERS
    threads = []
    kafka_producers = []

    # CREATE KAFKA PRODUCERS FOR EACH THREAD
    for _ in range(args['num_threads']):
        kafka_producer = create_producer(kafka_servers=kafka_servers)
        kafka_producers.append(kafka_producer)

    # MAKE SURE KAFKA CONNECTION IS OK
    if not kafka_producers[0].connected():
        return next(image_count)

    # LOAD THE DATASET
    dataset = load_dataset(args['dataset'])
    dataset_length = len(dataset)

    ########################################################################################
    ########################################################################################

    def experiment_handler(lock):
        global action_cooldown

        # THE DEFAULT DAYNIGHT CYCLE WORKLOAD PERCENTAGES (01 => 23)
        default_cycle = [
            0.03,   0.06,   0.09,   0.12,   0.266,  0.412,
            0.558,  0.704,  0.85,   0.7625, 0.675,  0.587,
            0.5,    0.59,   0.68,   0.77,   0.86,   0.97,
            0.813,  0.656,  0.5,    0.343,  0.186,  0.03
        ] * n_cycles

        #new linear cycle
        linear_cycle = []
        for x in range(1, 25):
            linear_cycle.append(x / 24)
        print(linear_cycle)
        # SCALE THE ARRAY WHILE MAINTAINING RATIOS
        real_cycle = resize_array(
            linear_cycle,
            args['experiment']['n_breakpoints']
        )

        # COMPUTE THE EQUAL TIME SLIVER
        time_sliver = args['experiment']['duration'] / args['experiment']['n_breakpoints']

        # COMPUTE THE BYTESIZE OF THE AVERAGE DATASET ITEM
        avg_dataset_item_size = math.ceil(sum([len(x) for x in dataset]) / len(dataset))

        log('STARTING EXPERIMENT WITH:')
        log(f'N_BREAKPOINTS: ({args["experiment"]["n_breakpoints"]})')
        log(f'MAX MB/s:  ({args["experiment"]["max_mbs"]})')
        log(f'TOTAL DURATION: ({args["experiment"]["duration"]})')
        log(f'SLIVER DURATION: ({time_sliver})')

        # STAY ACTIVE UNTIL LOCK IS MANUALLY KILLED
        while lock.is_active():

            # NO MORE BREAKPOINTS LEFT: KILL ALL THE THREADS
            if len(real_cycle) == 0:
                log('LAST EXPERIMENT BREAKPOINT RAN, TERMINATING..')
                lock.kill()
                break

            # OTHERWISE, FETCH THE NEXT INTERVAL
            mbs_interval = real_cycle.pop(0) * args['experiment']['max_mbs']
            log(f'SET NEW INPUT INTERVAL: ({time_sliver}s @ {mbs_interval} MB/s)')

            # COMPUTE THE NEW ACTION COOLDOWN
            events_per_second = (mbs_interval * 1000000) / avg_dataset_item_size
            new_cooldown = (1 / (events_per_second / args['num_threads']))

            # SAFELY SET THE NEXT COOLDOWN
            with semaphore:
                action_cooldown = new_cooldown

            # ON THE FIRST RUN, BUSY WAIT TO SYNC THREADS
            while time.time() < experiment_start:
                pass
            
            # THEN SLEEP UNTIL THE NEXT BREAKPOINT
            time.sleep(time_sliver)

    ########################################################################################
    ########################################################################################

    # PRODUCER THREAD WORK LOOP
    def thread_work(nth_thread, lock):
        global action_cooldown

        # RANDOMLY PICK A STARTING INDEX FROM THE DATASET
        next_index = random.randrange(dataset_length)
        cooldown = None

        # BUSY WAIT FOR ABIT TO SYNC THREADS
        while time.time() < experiment_start:
            pass

        log(f'THREAD {nth_thread} HAS STARTED FROM INDEX {next_index}')

        # KEEP GOING UNTIL LOCK IS MANUALLY
        while lock.is_active():
            started = time.time()

            # SELECT NEXT BUFFER ITEM
            image = dataset[next_index]
            img_as_bytes = image
            image_id = next(image_count)
            image_id_encoded = str(image_id).encode('utf-8')
            kafka_producers[nth_thread - 1].push_msg('yolo_input', img_as_bytes, key=image_id_encoded)
            
            # FETCH THE LATEST ACTION COOLDOWN
            with semaphore:
                cooldown = action_cooldown

            # COMPUTE THE ADJUSTED ACTION COOLDOWN, THEN TAKE A NAP
            ended = time.time()
            action_duration = ended - started
            adjusted_cooldown = max(cooldown - action_duration, 0)
            time.sleep(adjusted_cooldown)

            # INCREMENT ROLLING INDEX
            next_index = (next_index+1) % dataset_length

    ########################################################################################
    ########################################################################################

    try:
    
        # SHARED ACTION COOLDOWN FOR WORKER THREADS
        # TIMESTAMP FOR THREADS TO SYNC TO
        action_cooldown = None
        experiment_start = time.time() + 3

        # CREATE THE EXPERIMENT HANDLER
        log(f'CREATING EXPERIMENT HANDLER')
        handler_thread = Thread(target=experiment_handler, args=(thread_lock,))
        threads.append(handler_thread)
        handler_thread.start()

        log(f'CREATING PRODUCER THREAD POOL ({args["num_threads"]})')

        for nth in range(args['num_threads']):
            thread = Thread(target=thread_work, args=(nth+1, thread_lock))
            threads.append(thread)
            thread.start()

        # WAIT FOR EVERY THREAD TO FINISH (MUST BE MANUALLY KILLED BY CANCELING LOCK)
        [[thread.join() for thread in threads]]

    # TERMINATE MAIN PROCESS AND KILL HELPER THREADS
    except KeyboardInterrupt:
        thread_lock.kill()
        log('WORKER & THREADS MANUALLY KILLED..', True)

    return next(image_count)

if __name__ == '__main__':
    py_args = parser.parse_args()
    run(py_args.max_mbps, py_args.breakpoints, py_args.duration, py_args.n_cycles, py_args.compress)
