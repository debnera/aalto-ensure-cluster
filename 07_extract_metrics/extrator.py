import requests, pandas, json, os, shutil
from datetime import datetime
import time, math
from IPython.display import clear_output
from threading import Thread, Semaphore
import time, math, random, argparse, subprocess

def get_metric_names(port, exclude):
    try:
        result = requests.get(f'http://130.233.193.117:{port}/api/v1/label/__name__/values')
        container = []

        for metric in result.json()['data']:
            if not exclude(metric):
                container.append(metric)

        return container

    except:
        raise(f'COULD NOT PING INSTANCES AT PORT {port}')
        return False

def json_save(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def segment_timestamps(unix_start, unix_end, batch_size):

    container = []
    time_delta = unix_end - unix_start

    for _ in range(math.floor(time_delta / batch_size)):
        container.append(batch_size)
        time_delta -= batch_size

    if time_delta > 0:
        container.append(time_delta)

    last_start = unix_start
    tuples = []

    for window in container:
        tuples.append((last_start, last_start+window))
        last_start += window

    return tuples

def pad_print(items, n_spaces):
    container = ''

    for item in items[:-1]:
        padding = ' ' * (n_spaces - len(str(item)))
        container += str(item) + padding

    full_string = container + str(items[-1])
    print(full_string, flush=True)

class Tracker:
    def __init__(self, total):
        self.accumulator = Semaphore(1)
        self.value = 0
        self.total = total

        self.exp_start = time.time()

    def increment(self, query):
        self.accumulator.acquire()

        # COMPUTE THE DURATION BREAKPOINT
        duration = round(time.time() - self.exp_start, 2)

        # FORMAT DURATION
        if duration > 60:
            shortened = round(duration / 60, 2)
            duration = f'{shortened}m'
        else:
            duration = f'{duration}s'

        # INCREMENT COMPLETED LIST
        self.value += 1

        # SIGNAL THAT METRIC WAS COMPLETED
        percent = round((self.value/self.total) * 100, 2)
        nth_metric = f'{self.value}/{self.total} ({percent}%, {duration})'
        pad_print([nth_metric, query], 35)

        self.accumulator.release()

def path_bytes(path):
    shell_output = subprocess.check_output(['du', '-b', path]).decode('utf-8').split('\n')[-2].split('\tsnapshots/')
    num_bytes = shell_output[0]
    dir_name = shell_output[1]

    return int(num_bytes)

def fetch_metric(base_path, prometheus_port, query, formatted_start, formatted_end, n_steps, thread_lock, tracker):

    # CREATE SUB DIR FOR QUERY
    dir_path = f'{base_path}/{query}'
    os.mkdir(dir_path)

    # PROMETHEUS ONLY ALLOWS QUERIES WITH LESS THAN 11K ROWS
    # SEGMENT LARGE TIMESTAMPS INTO SMALLER PAIRS TO BYPASS THIS LIMITATION
    ts_segments = segment_timestamps(formatted_start, formatted_end, 2000)

    # LOOP THROUGH EACH SEGMENT, COMBINING THEIR QUERY OUTPUT
    for t1, t2 in ts_segments:

        # MAKE GET REQUEST
        URL = f'http://130.233.193.117:{prometheus_port}/api/v1/query_range?query={query}&start={t1}&end={t2}&step={n_steps}s'
        results = requests.get(URL).json()

        # SAVE THE JSON DUMP
        json_save(f'{dir_path}/{t1}-{t2}.json', results)

    # INCREMENT THE TRACKER & MAKE ROOM FOR THE NEXT THREAD
    tracker.increment(query)
    thread_lock.release()

def create_snapshot(start_time, end_time, n_steps):

    # GENERATE UNIQUE SNAPSHOT PATH & CREATE DIR FOR IT
    now = str(int(time.time()))
    snapshot_path = f'snapshots/{now}'
    os.mkdir(snapshot_path)

    # CONVERT DATES TO UNIX TIMESTAMPS
    date_format = '%Y-%m-%d %H:%M:%S'
    formatted_start = int(datetime.strptime(start_time, date_format).timestamp())
    formatted_end = int(datetime.strptime(end_time, date_format).timestamp())

    # PROMETHEUS SERVER 1 METRICS
    s1_filter = lambda x: x.startswith('prometheus_') or x.startswith('grafana_') or x.startswith('alertmanager_')
    #s1_filter = lambda x: not x.startswith('kepler_')
    s1_port = 9090
    s1_metrics = get_metric_names(s1_port, s1_filter)

    # PROMETHEUS SERVER 2 METRICS
    s2_filter = lambda x: not x.startswith('kafka_')
    s2_port = 9091
    s2_metrics = get_metric_names(s2_port, s2_filter)

    # SAFELY MAKE REQUESTS CONCURRENTLY WITH SEMAPHORE PROTECTION
    thread_lock = Semaphore(5)
    n_metrics = len(s1_metrics) + len(s2_metrics)
    tracker = Tracker(n_metrics)
    threads = []

    # MAKE PROMETHEUS SERVER2 QUERIES
    for metric in s1_metrics:
        thread_lock.acquire()
        thread = Thread(target=fetch_metric, args=(snapshot_path, s1_port, metric, formatted_start, formatted_end, n_steps, thread_lock, tracker))
        threads.append(thread)
        thread.start()

    # MAKE PROMETHEUS SERVER2 QUERIES
    for metric in s2_metrics:
        thread_lock.acquire()
        thread = Thread(target=fetch_metric, args=(snapshot_path, s2_port, metric, formatted_start, formatted_end, n_steps, thread_lock, tracker))
        threads.append(thread)
        thread.start()

    # WAIT FOR ALL THREADS TO FINISH
    [thread.join() for thread in threads]

    # FINALLY, PRINT OUT EXTRACTION STATS
    delta_time = round(time.time() - tracker.exp_start, 2)
    num_bytes = path_bytes(snapshot_path)
    num_mbs = round(num_bytes / 10**6, 2)

    print('', flush=True)
    pad_print(['EXTRACTION DURATION:', f'{delta_time}s'], 35)
    pad_print(['SNAPSHOT PATH:', snapshot_path], 35)
    pad_print(['SNAPSHOT BYTES:', f'{num_bytes} ({num_mbs} MB)'], 35)

#create_snapshot('2024-01-24 12:52:00', '2024-01-24 13:52:00', 5)
#create_snapshot('2024-01-24 01:00:00', '2024-01-24 09:00:00', 5)

# create_snapshot('2024-01-24 23:13:08', '2024-01-25 07:13:08', 5)

#create_snapshot('2024-01-26 02:54:43', '2024-01-26 10:54:43', 5)

# create_snapshot('2024-01-29 13:25:30', '2024-01-29 21:25:30', 10)

# create_snapshot('2024-01-29 22:56:30', '2024-01-30 06:56:30', 15)


# create_snapshot('2024-01-30 08:55:45', '2024-01-30 16:55:45', 5)

# create_snapshot('2024-01-30 19:10:15', '2024-01-31 03:10:15', 5)

create_snapshot('2024-01-31 05:05:00', '2024-01-31 09:05:00', 5)