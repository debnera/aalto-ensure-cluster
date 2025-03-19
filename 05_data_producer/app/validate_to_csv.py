import os

from utilz.kafka_utils import create_consumer
from utilz.misc import custom_deserializer, log, create_lock
from prometheus_client import Counter, Histogram, start_http_server
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

# PROMETHEUS METRICS
yolo_count = Counter('yolo_requests_received', 'Number of processed yolo jobs')
yolo_pre_time = Histogram('yolo_pre_time', 'Job pre-processing time in seconds')
yolo_inference_time = Histogram('yolo_inference_time', 'Job inference time in seconds')
yolo_post_time = Histogram('yolo_post_time', 'Job post-processing time in seconds')
# yolo_inference_time = Histogram('yolo_inference_time', 'Job processing time in seconds')
yolo_queue_time = Histogram('yolo_queue_time', 'Job queue time in seconds')



yolo_total_time_per_worker = Histogram('yolo_total_time_by_source', 'avg of work times for different workers', ['source'])


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

            # ONLY PROCESS YOLO INFERENCE RESULTS (this is for each pod?!)
            response[key]['min'] = round(min(data[key]['inf']), 2)
            response[key]['max'] = round(max(data[key]['inf']), 2)
            response[key]['avg'] = round(sum(data[key]['inf']) / len(data[key]['inf']), 2)
            response[key]['avg_total'] = round((sum(data[key]['inf']) + sum(data[key]['pre']) + sum(data[key]['post']) + sum(data[key]['queue']) ) / len(data[key]['inf']), 2)
            
            

            # REMOVE CONTAINERS
            del response[key]['inf']
            del response[key]['pre']

        # FINALLY, PRINT THE FINDINGS
        print(json.dumps(response, indent=4))	

    def process_event(self, raw_bytes, nth_thread):

        # SERIALIZE THE YOLO RESULTS
        yolo_results = custom_deserializer(raw_bytes)
        print(yolo_results['timestamps'])
        source = yolo_results['source']
        model = yolo_results['model']
        dimensions = yolo_results['dimensions']
        pre = yolo_results['timestamps']['pre']
        inf = yolo_results['timestamps']['inf']
        post = yolo_results['timestamps']['post']
        queue = 10
        if 'queue' in yolo_results['timestamps'].keys():
            queue = yolo_results['timestamps']['queue']
        else:	
            print("theres soemthing sus going on here")
        
        start_time = yolo_results['timestamps']['start_time']
        end_time = yolo_results['timestamps']['end_time']

        # PUBLISH PROMETHEUS STATISTICS
        yolo_count.inc()
        yolo_pre_time.observe(pre)
        yolo_inference_time.observe(inf)
        yolo_post_time.observe(post)
        yolo_queue_time.observe(queue)
        
        

        dat = copy.deepcopy(self.history)
        for key in self.history.keys():
            # SKIP NON-SOURCES
            if key == 'total_n':
                continue
            dat[key]['avg_total'] = round((sum(dat[key]['inf']) + sum(dat[key]['pre']) + sum(dat[key]['post']) + sum(dat[key]['queue']) ) / len(dat[key]['inf']), 2)
            yolo_total_time_per_worker.labels(source=key).observe(dat[key]['avg_total'])	
        
        

        # CREATE NEW CSV ROW
        self.data_rows.append({
            'source': source,
            'model': model,
            'dimensions': dimensions,
            'pre': pre,
            'inf': inf,
            'post': post,
            'queue': queue,
            'start_time': start_time,
            'end_time': end_time
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
        self.history[source]['queue'][next_index] = queue

        # INCREMENT LOCAL & GLOBAL COUNTERS
        self.history[source]['n'] += 1
        self.history['total_n'] += 1

        # PRINT AGGREGATE VALUES EVERY FULL WINDOW
        if self.history['total_n'] % args.print_interval == 0:
            self.format_response(self.history)

        if len(self.data_rows) % args.save_interval == 0:
            self.save_to_csv(self.data_rows)
            self.data_rows.clear()


    def run(self):

        ########################################################################################
        ########################################################################################

        # CREATE KAFKA CLIENTS
        kafka_consumer = create_consumer(args.input_topic)
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
            'post': [0] * args.print_interval,
            'queue': [0] * args.print_interval,
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
    start_http_server(8000)
    validator = Validator()
    validator.run()
    #validator.save_to_csv([{"a":1, "b":1},{"a":2, "b":2}])


