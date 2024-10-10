from typing import NamedTuple, Dict
from multiprocessing import Queue
import h5py, json
from .misc import log

# DATASET FRAME STRUCT
class Frame(NamedTuple):
    frame_number: int
    max_frames: int
    total_sensors: int  
    data: Dict[str, bytes]

# READ & PARSE HDF5 DATASET
def parse_dataset(args, buffer: Queue, thread_lock):

    # EXTRACT DATASET COMPONENTS
    dataset = h5py.File(f'./datasets/{args["name"]}.hdf5', 'r')
    activity = dataset['is_enabled']
    sensors = dataset['sensors']
    total_sensors = len(sensors.keys())
    metadata = json.loads(dataset['metadata'][()])
    n_frames = metadata["n_frames"]

    # COLLECT SENSOR COMPONENTS
    for nth in range(args['repeat']):
        sensor_names = list(dataset["sensors"].keys())
        sensor_data_iters = {key: iter(sensors[key]) for key in sensor_names}

        if args['max_frames'] > 0:
            n_frames = min(n_frames, args['max_frames'])

        for frame in range(n_frames):
            frame_data = {}

            if not thread_lock.is_active():
                break

            # FILL THE CURRENT FRAME
            for sensor_name, data_iter in sensor_data_iters.items():
                active = activity[sensor_name][frame]

                # Sensor has data for this frame only if it is marked as active
                if active:
                    sensor_data = next(data_iter)
                    frame_data[sensor_name] = sensor_data

            # CREATE FRAME STRUCT
            frame_wrapper = Frame(
                frame_number=frame,
                max_frames=n_frames,
                data=frame_data,
                total_sensors=total_sensors
            )

            # PUSH IT TO THE BUFFER -- WHEN THERE IS SPACE
            buffer.put(frame_wrapper, block=True)

        log(f'DATASET ITERATION ({nth+1}) DONE')

    log('DATASET FULLY PARSED')
    dataset.close()

def load_dataset(args):
    container = []

    # EXTRACT DATASET COMPONENTS
    dataset = h5py.File(f'{args["dataset_path"]}', 'r')
    activity = dataset['is_enabled']
    sensors = dataset['sensors']
    total_sensors = len(sensors.keys())
    metadata = json.loads(dataset['metadata'][()])
    n_frames = metadata["n_frames"]

    # COLLECT SENSOR COMPONENTS
    for nth in range(args['repeat']):
        sensor_names = list(dataset["sensors"].keys())
        sensor_data_iters = {key: iter(sensors[key]) for key in sensor_names}

        if args['max_frames'] > 0:
            n_frames = min(n_frames, args['max_frames'])

        for frame in range(n_frames):
            frame_data = {}

            # FILL THE CURRENT FRAME
            for sensor_name, data_iter in sensor_data_iters.items():
                active = activity[sensor_name][frame]

                # Sensor has data for this frame only if it is marked as active
                if active:
                    sensor_data = next(data_iter)
                    frame_data[sensor_name] = sensor_data

                    container.append(sensor_data)

    dataset.close()
    return container