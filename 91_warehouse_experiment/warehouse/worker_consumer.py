import logging
import os
import socket
import time

from utils.kafka_utils import create_consumer, create_producer
from utils.misc import custom_serializer, log, create_lock

from utils.worker_functions import local_to_world_space, process_point_cloud
from utils.lidar_frame import LidarFrame

errors = 0


def run():
    # Dynamic arguments for YOLO processing
    args = {
        'validate_results': os.environ.get('VALIDATE_RESULTS', 'TRUE') == 'TRUE',
        'kafka_input': os.environ.get('KAFKA_INPUT_TOPIC', 'grid_worker_input'),
        'kafka_output': os.environ.get('KAFKA_OUTPUT_TOPIC', 'grid_master_input'),
        'kafka_validate': os.environ.get('KAFKA_VALIDATE_TOPIC', 'grid_worker_validate'),
        'kafka_servers': os.environ.get('KAFKA_SERVERS', 'localhost:10001,localhost:10002'),
        'VERBOSE': os.environ.get('VERBOSE', 'FALSE') == 'TRUE',

    }
    logging.basicConfig(filename='grid_worker_log.log', level=logging.DEBUG)
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


    def process_event(data_bytes, msg_key, time_received, time_sent):
        global errors
        nonlocal idle_timer
        queue_time = time_received - time_sent  # How long was the message waiting in queue?
        msg_id = msg_key.decode('utf-8')

        if args['VERBOSE']:
            log(f"Message {msg_id} received! Queue_time: {queue_time} ms, size {len(data_bytes)} bytes.")
        t_idle = (time.time() - idle_timer) * 1000

        # Preprocessing
        t1 = time.time()
        frame = LidarFrame.from_bytes(data_bytes)
        world_space_lidar = local_to_world_space(frame.data, frame.position, frame.rotation)
        t_pre = (time.time() - t1) * 1000

        # Inference
        t2 = time.time()
        update_grid = process_point_cloud(world_space_lidar, frame.position)
        t_inf = (time.time() - t2) * 1000

        # Postprocessing
        t3 = time.time()
        update_bytes = update_grid.to_bytes()
        kafka_producer.push_msg(args['kafka_output'], update_bytes, key=msg_key)
        t_post = (time.time() - t3) * 1000

        idle_timer = time.time()  # Do not count pushing results to idle timer

        # Push results into validation topic if needed
        if args['validate_results']:
            kafka_producer.push_msg(args['kafka_validate'], custom_serializer({
                'timestamps': {
                    'idle': t_idle,  # Time spent waiting for next message
                    'pre': t_pre,
                    'inf': t_inf,
                    'post': t_post,
                    'queue': queue_time,
                    'start_time': time_sent,
                    'end_time': time_received
                },
                'id': msg_id,
                'errors': errors,
                'source': ip_addr,
            }))
        # print("Errors:", errors)

    # Create & start worker threads
    try:
        kafka_consumer.poll_next(1, thread_lock, process_event)
    except KeyboardInterrupt:
        thread_lock.kill()
        log('Worker manually killed.', True)
    except Exception as e:
        log(f'Exception: {e}', True)
        print(e)


run()
