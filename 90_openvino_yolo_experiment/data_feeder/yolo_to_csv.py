import os

import pandas as pd
import json, copy

class YoloToCSV:

    output_counter = 0
    def __init__(self, output_path=None, print_interval=20, save_interval=1000):
        self.output_path = output_path
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        self.print_interval = print_interval
        self.save_interval = save_interval
        # TRACK YOLO RESULTS
        self.history = {
            'total_n': 0
        }
        self.data_rows = []

        # SOURCE DEFAULT VALUES
        self.default = {
            'pre': [0] * self.print_interval,
            'inf': [0] * self.print_interval,
            'post': [0] * self.print_interval,
            'queue': [0] * self.print_interval,
            'n': 0,
        }

    def save_to_csv(self):
        if len(self.data_rows) == 0:
            print(f"Nothing to save to yolo csv {self.output_path}")
            return
        if self.output_path is None:
            print(f"Cannot save yolo csv to {self.output_path}")
            return
        df = pd.DataFrame(self.data_rows)
        df.to_csv(os.path.join(self.output_path, f"{self.output_counter}.csv"))
        self.output_counter += 1
        self.data_rows = []


    def __del__(self):
        self.save_to_csv()

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
        # print(json.dumps(response, indent=4))

    def process_event(self, msg_dict):

        # SERIALIZE THE YOLO RESULTS
        # yolo_results = custom_deserializer(raw_bytes)
        yolo_results = msg_dict
        # print(yolo_results['timestamps'])
        source = yolo_results['source']
        model = yolo_results['model']
        dimensions = yolo_results['dimensions']
        img_id = yolo_results['id']
        idle = yolo_results['timestamps']['idle']
        pre = yolo_results['timestamps']['pre']
        inf = yolo_results['timestamps']['inf']
        post = yolo_results['timestamps']['post']
        queue = yolo_results['timestamps']['queue']

        start_time = yolo_results['timestamps']['start_time']
        end_time = yolo_results['timestamps']['end_time']

        dat = copy.deepcopy(self.history)
        for key in self.history.keys():
            # SKIP NON-SOURCES
            if key == 'total_n':
                continue
            dat[key]['avg_total'] = round((sum(dat[key]['inf']) + sum(dat[key]['pre']) + sum(dat[key]['post']) + sum(dat[key]['queue']) ) / len(dat[key]['inf']), 2)
        
        

        # CREATE NEW CSV ROW
        self.data_rows.append({
            'source': source,
            'model': model,
            'dimensions': dimensions,
            'idle': idle,
            'pre': pre,
            'inf': inf,
            'post': post,
            'queue': queue,
            'start_time': start_time,
            'end_time': end_time,
            'id': img_id,
        })

        # ADD SOURCE IF IT DOESNT ALREADY EXIST
        if source not in self.history:
            self.history[source] = copy.deepcopy(self.default)

        # FIND NEXT ROLLING INDEX
        next_index = self.history[source]['n'] % self.print_interval

        # PUSH YOLO RESULTS
        self.history[source]['pre'][next_index] = pre
        self.history[source]['inf'][next_index] = inf
        self.history[source]['post'][next_index] = post
        self.history[source]['queue'][next_index] = queue

        # INCREMENT LOCAL & GLOBAL COUNTERS
        self.history[source]['n'] += 1
        self.history['total_n'] += 1

        # PRINT AGGREGATE VALUES EVERY FULL WINDOW
        if self.history['total_n'] % self.print_interval == 0:
            self.format_response(self.history)

        if len(self.data_rows) % self.save_interval == 0:
            self.save_to_csv()



