import utilz
import requests, os, time, argparse
from datetime import datetime
from threading import Thread, Semaphore

def process_metric(base_path: str, prometheus_endpoint: str, query: str, formatted_start: int, formatted_end: int, sampling: int, segment_size: int, thread_lock, tracker):

    # CREATE SUB DIR FOR QUERY
    dir_path = f'{base_path}/{query}'
    os.mkdir(dir_path)

    # PROMETHEUS ONLY ALLOWS QUERIES WITH LESS THAN 11K ROWS
    # SEGMENT LARGE TIMESTAMPS INTO SMALLER PAIRS TO BYPASS THIS LIMITATION
    ts_segments = utilz.segment_timestamps(formatted_start, formatted_end, segment_size)

    # LOOP THROUGH EACH SEGMENT, COMBINING THEIR QUERY OUTPUT
    for t1, t2 in ts_segments:

        # MAKE GET REQUEST
        URL = f'http://{prometheus_endpoint}/api/v1/query_range?query={query}&start={t1}&end={t2}&step={sampling}s'
        results = requests.get(URL).json()

        # SAVE THE JSON DUMP
        utilz.json_save(f'{dir_path}/{t1}-{t2}.json', results)

    # INCREMENT THE TRACKER & MAKE ROOM FOR THE NEXT THREAD
    tracker.increment(query)
    thread_lock.release()

def create_snapshot(start_time: str, end_time: str, sampling: int, segment_size: int, n_threads: int):

    # GENERATE UNIQUE SNAPSHOT PATH & CREATE DIR FOR IT
    now = str(int(time.time()))
    snapshot_path = f'snapshots/{now}'
    os.mkdir(snapshot_path)

    # CONVERT DATES TO UNIX TIMESTAMPS
    date_format = '%Y-%m-%d %H:%M:%S'
    formatted_start = int(datetime.strptime(start_time, date_format).timestamp())
    formatted_end = int(datetime.strptime(end_time, date_format).timestamp())

    # PROMETHEUS SERVER 1 METRICS
    # FILTER: EXCLUDE PROMETHEUS, GRAFANA AND ALERTMANAGER METRICS
    s1_filter = lambda metric: metric.startswith('prometheus_') or metric.startswith('grafana_') or metric.startswith('alertmanager_')
    s1_endpoint = 'localhost:9090'
    s1_metrics = utilz.get_metric_names(s1_endpoint, s1_filter)

    # PROMETHEUS SERVER 2 METRICS
    # FILTER: ONLY INCLUDE KAFKA METRICS
    s2_filter = lambda metric: not metric.startswith('kafka_')
    s2_endpoint = 'localhost:9091'
    s2_metrics = utilz.get_metric_names(s2_endpoint, s2_filter)

    # SAFELY MAKE REQUESTS CONCURRENTLY WITH SEMAPHORE PROTECTION
    thread_lock = Semaphore(n_threads)
    n_metrics = len(s1_metrics) + len(s2_metrics)
    tracker = utilz.Tracker(n_metrics)
    threads = []

    # MAKE PROMETHEUS SERVER2 QUERIES
    for metric in s1_metrics:
        thread_lock.acquire()

        thread = Thread(target=process_metric, args=(
            snapshot_path, 
            s1_endpoint, 
            metric, 
            formatted_start, 
            formatted_end, 
            sampling,
            segment_size,
            thread_lock, 
            tracker
        ))

        threads.append(thread)
        thread.start()

    # MAKE PROMETHEUS SERVER2 QUERIES
    for metric in s2_metrics:
        thread_lock.acquire()

        thread = Thread(target=process_metric, args=(
            snapshot_path, 
            s2_endpoint, 
            metric, 
            formatted_start, 
            formatted_end, 
            sampling, 
            segment_size,
            thread_lock, 
            tracker
        ))

        threads.append(thread)
        thread.start()

    # WAIT FOR ALL THREADS TO FINISH
    [thread.join() for thread in threads]

    # FINALLY, PRINT OUT EXTRACTION STATS
    delta_time = round(time.time() - tracker.exp_start, 2)
    num_bytes = utilz.path_bytes(snapshot_path)
    num_mbs = round(num_bytes / 10**6, 2)

    print('', flush=True)
    utilz.pad_print(['EXTRACTION DURATION:', f'{delta_time}s'], 35)
    utilz.pad_print(['SNAPSHOT PATH:', snapshot_path], 35)
    utilz.pad_print(['SNAPSHOT BYTES:', f'{num_bytes} ({num_mbs} MB)'], 35)

#############################################################################################################################
#############################################################################################################################

# create_snapshot('2024-01-24 12:52:00', '2024-01-24 13:52:00', 5)
# create_snapshot('2024-01-24 01:00:00', '2024-01-24 09:00:00', 5)
# create_snapshot('2024-01-24 23:13:08', '2024-01-25 07:13:08', 5)
# create_snapshot('2024-01-26 02:54:43', '2024-01-26 10:54:43', 5)
# create_snapshot('2024-01-29 13:25:30', '2024-01-29 21:25:30', 10)
# create_snapshot('2024-01-29 22:56:30', '2024-01-30 06:56:30', 15)
# create_snapshot('2024-01-30 08:55:45', '2024-01-30 16:55:45', 5)
# create_snapshot('2024-01-30 19:10:15', '2024-01-31 03:10:15', 5)

# PARSE PYTHON ARGUMENTS
parser = argparse.ArgumentParser()

# PYTHON PARAMS
parser.add_argument("-s", "--start", type=str, help="Starting timestamp for the experiment",)
parser.add_argument("-e", "--end", type=str, help="Ending timestamp for the experiment",)
parser.add_argument("-r", "--sampling", type=int, help="Sampling rate in seconds",)
parser.add_argument("-z", "--segment_size", type=int, help="Segment size that Prometheus queries are broken into",)
parser.add_argument("-t", "--n_threads", type=int, help="Number of concurrent threads to use",)

py_args = parser.parse_args()
# extractor.py --start "2024-01-30 19:10:15" --end "2024-01-31 03:10:15" --sampling 5 --n_threads 5

create_snapshot(
    start_time=py_args.start,
    end_time=py_args.end,
    sampling=py_args.sampling,
    segment_size=py_args.segment_size,
    n_threads=py_args.n_threads
)
