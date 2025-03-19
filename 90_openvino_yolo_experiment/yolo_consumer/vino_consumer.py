import time

import numpy as np

from utilz.kafka_utils import create_consumer, create_producer
from utilz.misc import custom_serializer, resource_exists, log, create_lock
from PIL import Image
from numpy import asarray
import io, socket, os
import logging
from ultralytics import YOLO
import openvino as ov
import openvino.properties as props

errors = 0


def run():
    print("Running the new version!")

    # Dynamic arguments for YOLO processing
    args = {
        'model': os.environ.get('YOLO_MODEL', 'yolov8n'),
        'validate_results': os.environ.get('VALIDATE_RESULTS', 'TRUE') == 'TRUE',
        'kafka_input': os.environ.get('KAFKA_INPUT_TOPIC', 'yolo_input'),
        'kafka_output': os.environ.get('KAFKA_OUTPUT_TOPIC', 'yolo_output'),
        'kafka_servers': os.environ.get('KAFKA_SERVERS', 'localhost:10001,localhost:10002,localhost:10003'),
        'VERBOSE': os.environ.get('VERBOSE', 'FALSE') == 'TRUE',
        'resolution': os.environ.get('RESOLUTION', '640'),

    }
    print(args)

    logging.basicConfig(filename='yolo_log.log', level=logging.DEBUG)

    kafka_consumer = create_consumer(args['kafka_input'], kafka_servers=args['kafka_servers'])
    kafka_producer = create_producer(kafka_servers=args['kafka_servers'])

    # Check that Kafka is working
    if not kafka_producer.connected() or not kafka_consumer.connected():
        log(f'Could not connect Kafka producer or consumer!')
        return

    # Check that model exists
    model = args['model']
    if not os.path.exists(f"{model}_openvino_model"):
        # Fetch Yolo model from cloud
        yolo_ultralytics = YOLO(f"{model}.pt")
        # Export yolo to two different openvino formats (which one do we actually want?)
        yolo_ultralytics.export(format="openvino", imgsz=int(args['resolution']))
        yolo_ultralytics.export(format="onnx", imgsz=int(args['resolution']))

    # Set up openvino
    core = ov.Core()
    device = core.available_devices[0]
    log(f'Available devices: {core.available_devices}')
    non_compiled_model = core.read_model(f"{model}.onnx")
    config = {props.hint.performance_mode: props.hint.PerformanceMode.LATENCY}
    yolo_ov_core = core.compile_model(non_compiled_model, device, config)
    log(f'Loaded model ({args["model"]}) on device ({device})')
    # Track which machine (pod) is doing the processing
    hostname = socket.gethostname()
    ip_addr = socket.gethostbyname(hostname)
    idle_timer = time.time()

    # Consumer thread setup
    thread_lock = create_lock()


    def process_event(img_bytes, msg_key, time_received, time_sent):
        global errors
        nonlocal idle_timer
        queue_time = time_received - time_sent  # How long was the message waiting in queue?
        img_id = msg_key.decode('utf-8')

        if args['VERBOSE']:
            print(f"Image {img_id} received! Queue_time: {queue_time} ms, size {len(img_bytes)} bytes.")
        t_idle = time.time() - idle_timer
        t1 = time.time()
        # Preprocess: Fetch image
        img = Image.open(io.BytesIO(img_bytes))
        image_array = asarray(img)
        image_array = image_array.reshape((1, 3, 640, 640))
        resolution = int(args['resolution'])
        if resolution != 640:
            image_array = image_array.copy()  # Fix ownership of the image by copying
            image_array = image_array.resize((1, 3, int(args['resolution']), int(args['resolution'])))
        t_pre = (time.time() - t1) * 1000
        t2 = time.time()
        # Inference
        results = yolo_ov_core(image_array)
        t_inf = (time.time() - t2) * 1000
        if args['VERBOSE']:
            print(f"queue: {queue_time}, t_pre: {t_pre}, t_inf: {t_inf}")

        # Postprocess: (TODO: Does ultralytics library do postprocessing by itself?)

        idle_timer = time.time()  # Do not count pushing results to idle timer
        # Push results into validation topic if needed
        if args['validate_results']:
            kafka_producer.push_msg(args['kafka_output'], custom_serializer({
                'timestamps': {
                    'idle': t_idle,  # Time spent waiting for next image
                    'pre': t_pre,
                    'inf': t_inf,
                    'post': 0.0, # No postprocessing
                    'queue': queue_time,
                    'start_time': time_sent,
                    'end_time': time_received
                },
                'id': img_id,
                'errors': errors,
                'source': ip_addr,
                'model': args['model'],
                #'dimensions': results[0].orig_shape
                'dimensions': results[0].shape
            }))
        print("Errors:", errors)

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
