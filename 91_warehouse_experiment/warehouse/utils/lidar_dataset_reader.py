import json
from typing import List

import h5py
import numpy as np

from .lidar_frame import LidarFrame


def load_to_memory(dataset_path: str) -> List[List[LidarFrame]]:
    """ Return a list of Frames for each sensor. """
    with h5py.File(dataset_path, "r") as dataset:
        sensors = dataset["sensors"].keys()
        metadata = json.loads(dataset["metadata"][()])
        all_sensor_frames: List[List[LidarFrame]] = []
        for sensor in sensors:
            frames: List[LidarFrame] = []
            n_frames = len(dataset["sensors"][sensor])
            actor_id = metadata[sensor]["id"]
            total_bytes = 0
            for frame in range(n_frames):
                actor_index = list(dataset["state/id"][frame]).index(actor_id)
                rotation = dataset["state/rotation"][frame][actor_index]
                location = dataset["state/location"][frame][actor_index]
                sensor_data = dataset[f"sensors/{sensor}"][frame]
                total_bytes += sensor_data.nbytes
                frames.append(LidarFrame(sensor_data, rotation, location))
            print(f"Sensor {sensor}: {total_bytes / (1024 * 1024):.2f} MB")
            all_sensor_frames.append(frames)
    return all_sensor_frames

if __name__ == "__main__":
    x = load_to_memory("../../robots-4/points-per-frame-1000.hdf5")
    # load_to_memory("../../robots-4/points-per-frame-5000.hdf5")
    # load_to_memory("../../robots-4/points-per-frame-10000.hdf5")
    bb = x[0][0]
    print(bb)
    b = bb.to_bytes()
    print(b)
    c = LidarFrame.from_bytes(b)
    print(c)
    print(
        np.array_equal(bb.data, c.data) and
        np.array_equal(bb.rotation, c.rotation) and
        np.array_equal(bb.position, c.position)
    )
