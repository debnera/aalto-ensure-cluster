import math
import matplotlib.pyplot as plt
import time
from enum import Enum
from datetime import datetime
from collections import defaultdict
from numba import njit, prange

import numpy as np

from .grid import OccupancyGrid
from .grid_cell import CellState


# Define colors for visualization
STATE_COLORS = {
    CellState.UNKNOWN: (1.0, 1.0, 1.0, 0.0),  # White (transparent)
    CellState.EMPTY: (0.05, 0.58, 0.39, 0.8),  # Green
    CellState.OCCUPIED: (0.18, 0.2, 0.29, 0.8),  # Dark Blue
    CellState.VEHICLE: (0.87, 0.18, 0.15, 1.0),  # Red
}

class GridVisualizer:
    def __init__(self):
        self.fig = None
        self.ax = None

    def visualize_grid(self, grid: OccupancyGrid, animate=True) -> None:
        """
        Visualize the occupancy grid using matplotlib, updating the same figure.
        """
        if self.fig == None:
            self.fig, self.ax = plt.subplots(figsize=(8, 8))
            self.ax.set_aspect('equal')

        # Clear the current axes
        self.ax.cla()

        # Collect grid data for rendering
        x_coords = []
        y_coords = []
        colors = []

        for (x, y), cell in grid._cells.items():
            state, certainty = cell.current_state(time.time())
            color = STATE_COLORS[state]
            colors.append((*color[:3], certainty))  # Add transparency based on certainty
            x_coords.append(x)
            y_coords.append(y)

        # Draw the grid cells
        self.ax.scatter(
            x_coords, y_coords,
            s=10,  # Scale size of grid visualization; adjust as needed
            c=colors,
            marker='s'
        )
        self.ax.set_title("Occupancy Grid Visualization")
        self.ax.invert_yaxis()

        # Update the plot
        if animate:
            plt.pause(0.00001)  # Pause to allow for visualization updates