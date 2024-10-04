from utilz.kafka_utils import create_consumer, create_producer
from utilz.misc import custom_serializer, resource_exists, log, create_lock
from PIL import Image
from numpy import asarray
import numpy as np
import io, torch, socket, os
import logging
import time
from ultralytics import YOLO
errors = 0
def run():
    print("this is the new version!")
    # DYNAMIC ARGUMENTS FOR YOLO PROCESSING
    args = {
        'model': os.environ.get('YOLO_MODEL', 'yolov8n'),
        'open_vino': True if os.environ.get('OPEN_VINO', 'TRUE') == 'TRUE' else False,
        'validate_results': True if os.environ.get('VALIDATE_RESULTS', 'TRUE') == 'TRUE' else False,
        'kafka_input': 'yolo_input',
        'kafka_output': 'yolo_output',
    }
    print(args)
    logging.basicConfig(filename='yolo_log.log', level=logging.DEBUG)

    ########################################################################################
    ########################################################################################

    # MAKE SURE THE MODEL FILE EXISTS
    if not resource_exists(f'./models/{args["model"]}.pt'):
        return

    # CREATE KAFKA CLIENTS
    kafka_consumer = create_consumer(args['kafka_input'])
    kafka_producer = create_producer()
    #
    # # MAKE SURE KAFKA CONNECTIONS ARE OK
    if not kafka_producer.connected() or not kafka_consumer.connected():
        return

    #torch method
    #yolo_ultralytics = YOLO("yolov8n.pt")



    from openvino.runtime import Core
    model_path = "yolov8n_openvino_model/yolov8n.xml"
    core = Core()
    print(core.available_devices)
    # cpu method
    model = core.read_model(model=model_path)
    yolo_ov_ultralytics = core.compile_model(model=model, device_name="CPU")


    # gpu method
    #yolo_ov_ultralytics = core.compile_model(model=model, device_name="GPU")


    #Old method
    #yolo_ov_ultralytics = YOLO("yolov8n_openvino_model/", task="detect")

    device = "I hope this doesnt matter"
    log(f'LOADED MODEL ({args["model"]}) ON DEVICE ({device})')

    # TRACK WHICH MACHINE (POD) IS DOING THE PROCESSING
    hostname = socket.gethostname()
    ip_addr = socket.gethostbyname(hostname)

    # CONSUMER THREAD STUFF
    thread_lock = create_lock()

    ########################################################################################
    ########################################################################################

    # WHAT THE THREAD DOES WITH POLLED EVENTS
    def process_event(img_bytes, nth_thread, end, start):
        global errors
        # CONVERT INPUT BYTES TO IMAGE & GIVE IT THREAD SPECIFIC YOLO MODEL
        t1 = time.time()
        img = Image.open(io.BytesIO(img_bytes))
        image_array = asarray(img)
        image_array = np.repeat(image_array, 1)
        image_array = image_array.reshape((1, 3, 640, 640))
        t_pre = (time.time() - t1) * 1000
        t2 = time.time()
        results = yolo_ov_ultralytics(image_array)
        t_inf = (time.time() - t2) * 1000
        qt = end - start
        print("everything all right up to here right??!")
        # PUSH RESULTS INTO VALIDATION TOPIC
        if args['validate_results']:
            kafka_producer.push_msg(args['kafka_output'], custom_serializer({
                'timestamps': {
                    'pre': t_pre,
                    'inf': t_inf,
                    'post': 0.0,
                    'queue': qt,
                    'start_time': start,
                    'end_time': end
                },
                'source': ip_addr,
                'model': args['model'],
                #'dimensions': results[0].orig_shape
                'dimensions': results[0].shape
            }))
        print("errors:", errors)

    ########################################################################################
    ########################################################################################

    # CREATE & START WORKER THREADS
    try:
        kafka_consumer.poll_next(1, thread_lock, process_event)

    # TERMINATE MAIN PROCESS AND KILL HELPER THREADS
    except KeyboardInterrupt:
        thread_lock.kill()
        log('WORKER MANUALLY KILLED..', True)

run()
