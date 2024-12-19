import logging
import os
import socket
import time

import matplotlib.pyplot as plt

from utils.grid_visualize import GridVisualizer
from utils.grid import OccupancyGrid
from utils.kafka_utils import create_consumer, create_producer
from utils.misc import custom_serializer, log, create_lock

errors = 0


def run():
    args = {
        'validate_results': os.environ.get('VALIDATE_RESULTS', 'TRUE') == 'TRUE',
        'kafka_input': os.environ.get('KAFKA_INPUT_TOPIC', 'grid_master_input'),
        'kafka_validate': os.environ.get('KAFKA_VALIDATE_TOPIC', 'grid_master_validate'),
        'kafka_servers': os.environ.get('KAFKA_SERVERS', 'localhost:10001,localhost:10002,localhost:10003'),
        'VERBOSE': os.environ.get('VERBOSE', 'FALSE') == 'TRUE',
        'visualize': os.environ.get('VISUALIZE', 'TRUE') == 'TRUE',
    }

    logging.basicConfig(filename='gird_master_log.log', level=logging.DEBUG)
    log(args)

    kafka_consumer = create_consumer(args['kafka_input'], kafka_servers=args['kafka_servers'])
    kafka_producer = create_producer(kafka_servers=args['kafka_servers'])

    # Check that Kafka is working
    if not kafka_producer.connected() or not kafka_consumer.connected():
        log(f'Could not connect Kafka producer or consumer!')
        return

    # Track which machine (pod) is doing the processing
    hostname = socket.gethostname()
    ip_addr = socket.gethostbyname(hostname)
    idle_timer = time.time()

    # Consumer thread setup
    thread_lock = create_lock()

    # Setup application
    grid = OccupancyGrid()
    visualizer = GridVisualizer()

    def process_event(data_bytes, msg_key, time_received, time_sent):
        global errors
        nonlocal idle_timer
        queue_time = time_received - time_sent  # How long was the message waiting in queue?
        msg_id = msg_key.decode('utf-8')

        if args['VERBOSE']:
            log(f"Message {msg_id} received! Queue_time: {queue_time} ms, size {len(data_bytes)} bytes.")
        t_idle = (time.time() - idle_timer) * 1000
        t1 = time.time()
        grid.update_from_bytes(data_bytes, check_timestamp=True)
        t_inf = (time.time() - t1) * 1000

        # Postprocessing
        if args['visualize'] and int(msg_id) % 10 == 0:
            visualizer.visualize_grid(grid, animate=False)
            os.makedirs("visualizations", exist_ok=True)
            plt.savefig(f"visualizations/grid_update_{msg_id}.png")
            log(f"Saved visualization for message {msg_id}")
        idle_timer = time.time()  # Do not count pushing results to idle timer

        # Push results into validation topic if needed
        if args['validate_results']:
            kafka_producer.push_msg(args['kafka_validate'], custom_serializer({
                'timestamps': {
                    'idle': t_idle,  # Time spent waiting for next message
                    'pre': 0.0,  # No preprocessing
                    'inf': t_inf,
                    'post': 0.0,  # No postprocessing
                    'queue': queue_time,
                    'start_time': time_sent,
                    'end_time': time_received
                },
                'id': msg_id,
                'errors': errors,
                'source': ip_addr,
            }))
        # log("Errors:", errors)

    # Create & start worker threads
    try:
        kafka_consumer.poll_next(1, thread_lock, process_event)
    except KeyboardInterrupt:
        thread_lock.kill()
        log('Worker manually killed.', True)
    except Exception as e:
        log(f'Exception: {e}', True)
        log(e)


run()
