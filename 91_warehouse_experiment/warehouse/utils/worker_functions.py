import math
from concurrent.futures import ProcessPoolExecutor

import matplotlib.pyplot as plt
import time
from enum import Enum
from datetime import datetime
from collections import defaultdict
from numba import njit, prange

import numpy as np

from .grid import OccupancyGrid
from .grid_cell import CellState
from .grid_visualize import GridVisualizer


@njit
def bresenham_line_algorithm(x0, y0, x1, y1):
    """
    Bresenham's Line Algorithm for finding grid points between two coordinates.
    """
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        points.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

    return points


@njit
def process_points(sensor_position, point_cloud, cell_size_mm):
    """
    Numba-optimized function to calculate updates for grid processing.
    """
    updates = []
    sx, sy, sz = sensor_position

    for i in prange(point_cloud.shape[0]):
        gx, gy, gz = point_cloud[i]
        if gz < 20 or gz > 2000:
            continue

        hit_cell_x = int(gx // cell_size_mm)
        hit_cell_y = int(gy // cell_size_mm)
        empty_cells = bresenham_line_algorithm(
            int(sx // cell_size_mm),
            int(sy // cell_size_mm),
            hit_cell_x,
            hit_cell_y
        )
        updates.append(((hit_cell_x, hit_cell_y), empty_cells))

    return updates


def to_grid_space(value, cell_size_mm):
    """
    Convert world coordinates to grid coordinates.

    Args:
        value: The raw value in millimeters.
        cell_size_mm: The size of grid cells in millimeters.

    Returns:
        The grid-aligned coordinate.
    """
    return int(value // cell_size_mm) * cell_size_mm

def local_to_world_space(point_cloud, sensor_position, sensor_rotation):
    rotation = sensor_rotation.copy()
    rotation[1] += 90  # Fix rotation bug by adding +90 degrees to yaw
    location = sensor_position.copy()
    local_space_lidar = point_cloud.copy()
    yaw = rotation[1]  # NOTE: Remember the bug mentioned above! Extra +90 degrees had to be added to yaw!
    yaw = np.deg2rad(yaw)  # Convert degrees to radians
    rotation_matrix = np.array(((np.cos(yaw), -np.sin(yaw), 0),
                                (np.sin(yaw), np.cos(yaw), 0),
                                (0, 0, 1)))
    world_space_lidar = np.empty(local_space_lidar.shape)  # Preallocate array
    for i in range(local_space_lidar.shape[0]):
        # Transform all points in the point cloud
        world_space_lidar[i] = np.dot(rotation_matrix, local_space_lidar[i])  # Rotate
        world_space_lidar[i] += location  # Translate
    world_space_lidar *= 1000  # Meter to millimeter
    return world_space_lidar

def process_point_cloud(point_cloud, sensor_position):
    """
    Process a LiDAR point cloud and update the occupancy grid.
    """
    now = time.time()  # TODO: Time in seconds, nanoseconds or milliseconds?

    # Mark the vehicle's cell
    update_grid = OccupancyGrid()  # New grid where we will place all updates
    vehicle_cell = (
        to_grid_space(sensor_position[0], OccupancyGrid.GRID_CELL_SIZE_MM),
        to_grid_space(sensor_position[1], OccupancyGrid.GRID_CELL_SIZE_MM),
    )
    # grid.get_cell(*vehicle_cell).make_observation(CellState.VEHICLE, datetime.now())
    update_grid.get_cell(*vehicle_cell).make_observation(CellState.VEHICLE, now)

    # Use Numba-optimized function to compute updates
    updates = process_points(
        sensor_position * 1000, # Vehicle position to millimeters
        np.array(point_cloud),
        OccupancyGrid.GRID_CELL_SIZE_MM
    )

    # Apply updates to the grid
    for hit_cell, empty_cells in updates:
        update_grid.get_cell(*hit_cell).make_observation(CellState.OCCUPIED, now)
        for cell in empty_cells:
            update_grid.get_cell(*cell).make_observation(CellState.EMPTY, now)

    return update_grid


# Example Usage
if __name__ == "__main__":
    # Initialize the grid and LiDAR processor
    grid = OccupancyGrid()
    visualizer = GridVisualizer()

    # Simulate some LiDAR data (3D points in millimeters)
    lidar_data = [(1000 + i * 500, 2000 + j * 500, 300) for i in range(-5, 5) for j in range(-5, 5)]
    sensor_position = (1000, 2000, 300)

    # Process the LiDAR data
    # processor.process_point_cloud(lidar_data, sensor_position, visualize=True)

    import h5py, json

    data = h5py.File("../robots-4/points-per-frame-1000.hdf5", 'r')
    sensor_data = data["sensors/robot_1"]
    metadata = json.loads(data["metadata"][()])
    actor_id = metadata["robot_1"]["id"]  # Fetch ID for lidar of robot_1
    print("Robot_1 actor ID: " + str(actor_id))
    start_time = time.time()
    for i in range(1):
        for frame in range(1000):
            print("Processing frame " + str(frame))
            index = list(data["state/id"][frame]).index(actor_id)  # NOTE: All frames should contain the same ID
            rotation = data["state/rotation"][frame][index]
            location = data["state/location"][frame][index]
            local_space_lidar = data["sensors/robot_1"][frame]
            world_space_lidar = local_to_world_space(local_space_lidar, location, rotation)
            update_grid = process_point_cloud(world_space_lidar, location)
            update_bytes = update_grid.to_bytes()
            grid.update_from_bytes(update_bytes)
            visualizer.visualize_grid(grid)
    print("Time taken: " + str(time.time() - start_time))  # 91.89 seconds
