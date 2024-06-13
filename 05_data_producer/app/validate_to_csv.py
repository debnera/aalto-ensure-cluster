import os

from utilz.kafka_utils import create_consumer
from utilz.misc import custom_deserializer, log, create_lock
import pandas as pd
import json, copy
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--save_interval", type=int,
                    help="Number of result rows to save in a single csv file.",
                    default=200)
parser.add_argument("--print_interval", type=int,
                    help="Number of result rows included in a single print.",
                    default=20)
parser.add_argument("--input_topic", type=str,
                    help="Kafka topic to listen for yolo results.",
                    default="yolo_output")
parser.add_argument("--output_path", type=str,
                    help="Results will be saved to this directory",
                    default="./yolo_outputs/")
args = parser.parse_args()

class Validator:

    output_counter = 0

    def save_to_csv(self, rows):
        df = pd.DataFrame(rows)
        os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
        df.to_csv(os.path.join(args.output_path, f"{self.output_counter}.csv"))
        self.output_counter += 1

    def format_response(self, data):
        response = copy.deepcopy(data)

        for key in data.keys():

            # SKIP NON-SOURCES
            if key == 'total_n':
                continue

            # ONLY PROCESS YOLO INFERENCE RESULTS
            response[key]['min'] = round(min(data[key]['inf']), 2)
            response[key]['max'] = round(max(data[key]['inf']), 2)
            response[key]['avg'] = round(sum(data[key]['inf']) / len(data[key]['inf']), 2)

            # REMOVE CONTAINERS
            del response[key]['inf']
            del response[key]['pre']

        # FINALLY, PRINT THE FINDINGS
        print(json.dumps(response, indent=4))

    def process_event(self, raw_bytes):

        # SERIALIZE THE YOLO RESULTS
        yolo_results = custom_deserializer(raw_bytes)
        source = yolo_results['source']
        model = yolo_results['model']
        dimensions = yolo_results['dimensions']
        pre = yolo_results['timestamps']['pre']
        inf = yolo_results['timestamps']['inf']
        post = yolo_results['timestamps']['post']

        self.data_rows.append({
            'source': source,
            'model': model,
            'dimensions': dimensions,
            'pre': pre,
            'inf': inf,
            'post': post,
        })

        # ADD SOURCE IF IT DOESNT ALREADY EXIST
        if source not in self.history:
            self.history[source] = copy.deepcopy(self.default)

        # FIND NEXT ROLLING INDEX
        next_index = self.history[source]['n'] % args.print_interval

        # PUSH YOLO RESULTS
        self.history[source]['pre'][next_index] = pre
        self.history[source]['inf'][next_index] = inf
        self.history[source]['post'][next_index] = post

        # INCREMENT LOCAL & GLOBAL COUNTERS
        self.history[source]['n'] += 1
        self.history['total_n'] += 1

        # PRINT AGGREGATE VALUES EVERY FULL WINDOW
        if self.history['total_n'] % args.print_interval == 0:
            self.format_response(self.history)

        if len(self.data_rows) % args.save_interval == 0:
            self.save_to_csv(self.data_rows)
            data_rows = []

    def run(self):

        ########################################################################################
        ########################################################################################

        # CREATE KAFKA CLIENTS
        kafka_consumer = create_consumer(args['input_topic'])
        thread_lock = create_lock()

        # MAKE SURE KAFKA CONNECTIONS ARE OK
        if not kafka_consumer.connected():
            print("Could not connect to Kafka - exiting")
            return

        # TRACK YOLO RESULTS
        self.history = {
            'total_n': 0
        }
        self.data_rows = []

        # SOURCE DEFAULT VALUES
        self.default = {
            'pre': [0] * args.print_interval,
            'inf': [0] * args.print_interval,
            'n': 0,
        }



        # FORMAT HISTORICAL DATA

        # ON EVENT, DO..


        # FINALLY, START CONSUMING EVENTS
        try:
            kafka_consumer.poll_next(1, thread_lock, self.process_event)

        # TERMINATE MAIN PROCESS AND KILL HELPER THREADS
        except KeyboardInterrupt:
            thread_lock.kill()
            log('WORKER MANUALLY KILLED..', True)


if __name__ == '__main__':
    validator = Validator()
    validator.run()
    #validator.save_to_csv([{"a":1, "b":1},{"a":2, "b":2}])


