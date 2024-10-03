from utilz.kafka_utils import create_consumer, create_producer
from utilz.misc import custom_serializer, resource_exists, log, create_lock
from PIL import Image
from numpy import asarray
import io, torch, socket, os
import logging
from ultralytics import YOLO

errors = 0


def run():
    print("Running the new version!")

    # Dynamic arguments for YOLO processing
    args = {
        'model': os.environ.get('YOLO_MODEL', 'yolov8n'),
        'open_vino': os.environ.get('OPEN_VINO', 'TRUE') == 'TRUE',
        'validate_results': os.environ.get('VALIDATE_RESULTS', 'TRUE') == 'TRUE',
        'kafka_input': 'yolo_input',
        'kafka_output': 'yolo_output',
    }
    print(args)

    logging.basicConfig(filename='yolo_log.log', level=logging.DEBUG)

    # Make sure the model file exists
    if not resource_exists(f'./models/{args["model"]}.pt'):
        return

    # OpenVINO model setup
    from openvino.runtime import Core
    model_path = "yolov8n_openvino_model/yolov8n.xml"
    core = Core()
    print(core.available_devices)

    model = core.read_model(model=model_path)
    yolo_ov_ultralytics = core.compile_model(model=model, device_name="GPU")

    device = "Unknown device"
    log(f'Loaded model ({args["model"]}) on device ({device})')

    # Track which machine (pod) is doing the processing
    hostname = socket.gethostname()
    ip_addr = socket.gethostbyname(hostname)

    # Consumer thread setup
    thread_lock = create_lock()

    def process_event(img_bytes, nth_thread, end, start):
        global errors
        # Convert input bytes to image & apply YOLO model
        img = Image.open(io.BytesIO(img_bytes))
        results = yolo_ov_ultralytics(asarray(img))
        qt = end - start

        # Push results into validation topic if needed
        if args['validate_results']:
            kafka_producer.push_msg(args['kafka_output'], custom_serializer({
                'timestamps': {
                    'pre': results[0].speed['preprocess'],
                    'inf': results[0].speed['inference'],
                    'post': results[0].speed['postprocess'],
                    'queue': qt,
                    'start_time': start,
                    'end_time': end
                },
                'source': ip_addr,
                'model': args['model'],
                'dimensions': results[0].orig_shape
            }))
        print("Errors:", errors)

    # Create & start worker threads
    try:
        kafka_consumer.poll_next(1, thread_lock, process_event)
    except KeyboardInterrupt:
        thread_lock.kill()
        log('Worker manually killed.', True)


run()
