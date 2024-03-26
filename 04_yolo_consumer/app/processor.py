from utilz.kafka_utils import create_consumer, create_producer
from utilz.misc import custom_serializer, resource_exists, log, create_lock
from PIL import Image
from numpy import asarray
import io, torch, socket, os, logging

def run():

    args = {

        # SPECIFY DEFAULT VALUES
        # NOTE THAT THESE CAN BE FILLED BY PROGRAM ARGUMENTS
        'model': os.environ.get('YOLO_MODEL', 'custom-750k'),
        'validate_results': True if os.environ.get('VALIDATE_RESULTS', 'TRUE') == 'TRUE' else False,
        
        # KAFKA TOPIC NAMES
        'kafka_input': 'yolo_input',
        'kafka_output': 'yolo_output',
    }

    # CREATE A PERMANENT LOGFILE
    logging.basicConfig(filename='yolo_logs.log', encoding='utf-8', level=logging.DEBUG)

    ########################################################################################
    ########################################################################################

    # MAKE SURE THE MODEL FILE EXISTS
    if not resource_exists(f'./models/{args["model"]}.pt'):
        return

    # CREATE KAFKA CLIENTS
    kafka_consumer = create_consumer(args['kafka_input'])
    kafka_producer = create_producer()

    # MAKE SURE KAFKA CONNECTIONS ARE OK
    if not kafka_producer.connected() or not kafka_consumer.connected():
        return

    # LOAD THE INTENDED YOLO MODEL
    yolo_model = torch.hub.load('ultralytics/yolov5', 'custom', path=f'./models/{args["model"]}.pt', trust_repo=True, force_reload=True)
    device = yolo_model.parameters().__next__().device
    log(f'LOADED MODEL ({args["model"]}) ON DEVICE ({device})')

    # TRACK WHICH MACHINE (POD) IS DOING THE PROCESSING
    hostname = socket.gethostname()
    ip_addr = socket.gethostbyname(hostname)

    # CONSUMER THREAD STUFF
    thread_lock = create_lock()

    ########################################################################################
    ########################################################################################

    # WHAT THE THREAD DOES WITH POLLED EVENTS
    def process_event(img_bytes, nth_thread):

        # CONVERT INPUT BYTES TO IMAGE & GIVE IT THREAD SPECIFIC YOLO MODEL
        img = Image.open(io.BytesIO(img_bytes))
        results = yolo_model.forward(asarray(img))

        # PUSH RESULTS INTO VALIDATION TOPIC
        if args['validate_results']:
            kafka_producer.push_msg(args['kafka_output'], custom_serializer({
                'timestamps': {
                    'pre': results.t[0],
                    'inf': results.t[1],
                    'post': results.t[2],
                },
                'source': ip_addr,
                'model': args['model'],
                'dimensions': results.s
            }))

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