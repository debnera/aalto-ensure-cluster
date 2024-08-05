from utilz.kafka_utils import create_consumer
from utilz.misc import custom_deserializer, log, create_lock
import json, copy

def run():

    # DYNAMIC ARGS
    args = {
        'window_size': 20,
        'input_topic': 'yolo_output',
    }

    ########################################################################################
    ########################################################################################

    # CREATE KAFKA CLIENTS
    kafka_consumer = create_consumer(args['input_topic'])
    thread_lock = create_lock()

    # MAKE SURE KAFKA CONNECTIONS ARE OK
    if not kafka_consumer.connected():
        return

    # TRACK YOLO RESULTS
    history = {
        'total_n': 0
    }

    # SOURCE DEFAULT VALUES
    default = {
        'pre': [0] * args['window_size'],
        'inf': [0] * args['window_size'],
        'n': 0,
    }

    # FORMAT HISTORICAL DATA
    def format_response(data):
        response = copy.deepcopy(data)

        for key in data.keys():

            # SKIP NON-SOURCES
            if key == 'total_n': continue

            # # EXTRACT MIN, MAX AND AVG VALUES FROM EACH CATEGORY
            # for category in ['inf', 'pre']:
            #     response[key][category] = {
            #         'min': round(min(data[key][category]), 2),
            #         'max': round(max(data[key][category]), 2),
            #         'avg': round(sum(data[key][category]) / len(data[key][category]), 2),
            #     }

            # ONLY PROCESS YOLO INFERENCE RESULTS
            response[key]['min'] = round(min(data[key]['inf']), 2)
            response[key]['max'] = round(max(data[key]['inf']), 2)
            response[key]['avg'] = round(sum(data[key]['inf']) / len(data[key]['inf']), 2)

            # REMOVE CONTAINERS
            del response[key]['inf']
            del response[key]['pre']

        # FINALLY, PRINT THE FINDINGS
        print(json.dumps(response, indent=4))

    # ON EVENT, DO..
    def process_event(raw_bytes):

        # SERIALIZE THE YOLO RESULTS
        yolo_results = custom_deserializer(raw_bytes)
        source = yolo_results['source']
        pre = yolo_results['timestamps']['pre']
        inf = yolo_results['timestamps']['inf']

        # ADD SOURCE IF IT DOESNT ALREADY EXIST
        if source not in history:
            history[source] = copy.deepcopy(default)

        # FIND NEXT ROLLING INDEX
        next_index = history[source]['n'] % args['window_size']

        # PUSH YOLO RESULTS
        history[source]['pre'][next_index] = pre
        history[source]['inf'][next_index] = inf
        
        # INCREMENT LOCAL & GLOBAL COUNTERS
        history[source]['n'] += 1
        history['total_n'] += 1

        # PRINT AGGREGATE VALUES EVERY FULL WINDOW
        if history['total_n'] % args['window_size'] == 0:
            format_response(history)

    # FINALLY, START CONSUMING EVENTS
    try:
        kafka_consumer.poll_next(1, thread_lock, process_event)

    # TERMINATE MAIN PROCESS AND KILL HELPER THREADS
    except KeyboardInterrupt:
        thread_lock.kill()
        log('WORKER MANUALLY KILLED..', True)

run()
