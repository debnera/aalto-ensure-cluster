import requests, json, math, time, subprocess
from threading import Semaphore

# READ ALL AVAILABLE METRICS FROM PROMETHEUS ENDPOINT
def get_metric_names(endpoint, excluding_func):
    try:
        result = requests.get(f'http://{endpoint}/api/v1/label/__name__/values')
        container = []

        # EXCLUDE CERTAIN METRICS
        for metric in result.json()['data']:
            if not excluding_func(metric):
                container.append(metric)

        return container

    except:
        raise(f'COULD NOT PING ENDPOINT ({endpoint})')
        return False

# SAVE DICT TO JSON FILE
def json_save(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# SPLIT EXPERIMENT DURATION INTO N SEGMENTS
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

# PAD PRINT STRINGS
def pad_print(items, n_spaces):
    container = ''

    for item in items[:-1]:
        padding = ' ' * (n_spaces - len(str(item)))
        container += str(item) + padding

    full_string = container + str(items[-1])
    print(full_string, flush=True)

# TRACK EXPERIMENT PROGRESS
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

# MEASURE NUM BYTES IN PATH
def path_bytes(path):
    shell_output = subprocess.check_output(['du', '-b', path]).decode('utf-8').split('\n')[-2].split('\tsnapshots/')
    num_bytes = shell_output[0]
    dir_name = shell_output[1]

    return int(num_bytes)