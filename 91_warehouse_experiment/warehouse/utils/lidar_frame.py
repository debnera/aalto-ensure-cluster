import numpy as np


class LidarFrame:
    def __init__(self, data: np.array, rotation: np.array, position: np.array):
        if data.dtype != np.float32 or rotation.dtype != np.float32 or position.dtype != np.float32:
            raise TypeError("All inputs must be of type float32")
        self.data = data
        self.rotation = rotation
        self.position = position

    def to_bytes(self) -> bytes:
        return b''.join([
            self.data.tobytes(),
            self.rotation.tobytes(),
            self.position.tobytes()
        ])

    @staticmethod
    def from_bytes(data_bytes: bytes) -> 'LidarFrame':
        rotation_shape = position_shape = (3,)
        rotation_size = np.prod(rotation_shape) * np.dtype(np.float32).itemsize
        position_size = np.prod(position_shape) * np.dtype(np.float32).itemsize

        offset = len(data_bytes) - rotation_size - position_size
        data_shape = (offset // (np.dtype(np.float32).itemsize * 3), 3)

        data_array = np.frombuffer(data_bytes[:offset], dtype=np.float32).reshape(data_shape)
        rotation_array = np.frombuffer(data_bytes[offset:offset + rotation_size], dtype=np.float32).reshape(
            rotation_shape)
        position_array = np.frombuffer(data_bytes[offset + rotation_size:], dtype=np.float32).reshape(position_shape)

        return LidarFrame(data_array, rotation_array, position_array)
