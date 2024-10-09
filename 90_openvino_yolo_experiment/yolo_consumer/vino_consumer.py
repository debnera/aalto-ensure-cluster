import time

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
        'kafka_servers': os.environ.get('KAFKA_SERVERS', 'localhost:10001,localhost:10002,localhost:10003')
    }
    print(args)

    logging.basicConfig(filename='yolo_log.log', level=logging.DEBUG)

    kafka_consumer = create_consumer(args['kafka_input'])
    kafka_producer = create_producer()

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
        yolo_ultralytics.export(format="openvino")
        yolo_ultralytics.export(format="onnx")

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

    # Consumer thread setup
    thread_lock = create_lock()


    def process_event(img_bytes, nth_thread, time_received, time_sent):
        global errors
        queue_time = time_received - time_sent  # How long was the message waiting in queue?
        t1 = time.time()
        # Preprocess: Fetch image
        img = Image.open(io.BytesIO(img_bytes))
        image_array = asarray(img)
        image_array = image_array.reshape((1, 3, 640, 640))
        t_pre = (time.time() - t1) * 1000
        t2 = time.time()
        # Inference
        results = yolo_ov_core(image_array)
        t_inf = (time.time() - t2) * 1000

        # Postprocess: (TODO: Does ultralytics library do postprocessing by itself?)

        # Push results into validation topic if needed
        if args['validate_results']:
            kafka_producer.push_msg(args['kafka_output'], custom_serializer({
                'timestamps': {
                    'pre': t_pre,
                    'inf': t_inf,
                    'post': 0.0, # No postprocessing
                    'queue': queue_time,
                    'start_time': time_sent,
                    'end_time': time_received
                },
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


run()
