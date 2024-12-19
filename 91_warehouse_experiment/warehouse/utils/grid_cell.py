import math
from collections import defaultdict
from enum import Enum

import numpy as np
from numba import njit


# Enum for Cell States

class CellState(Enum):
    UNKNOWN = 0
    EMPTY = 1
    OCCUPIED = 2
    VEHICLE = 3


@njit
def compute_certainty_numba(states, elapsed_times, decay_constants):
    """
    Compute certainty for each state using exponential decay.
    This replaces the Python dictionary with arrays for compatibility.

    Args:
        states: List or array of state enum indices (e.g., [1, 2, 3]).
        elapsed_times: Corresponding list of elapsed times in seconds.
        decay_constants: Array of decay constants, indexed by state.

    Returns:
        A tuple containing (most_likely_state_index, confidence_value).
    """
    state_probabilities = np.empty(len(states))
    for i in range(len(states)):
        state = states[i]
        elapsed_time = elapsed_times[i]
        state_probabilities[i] = math.exp(-decay_constants[state] * elapsed_time)

    most_likely_state_idx = np.argmax(state_probabilities)
    return states[most_likely_state_idx], state_probabilities[most_likely_state_idx]


class GridCell:
    def __init__(self) -> None:
        """Initialize a grid cell with no observations and unknown state."""
        self._observations: dict[CellState, float] = defaultdict(float)  # {state: timestamp}

    def make_observation(self, state: CellState, time: float) -> None:
        """
        Record an observation for the grid cell.

        Args:
            state: The observed CellState.
            time: The time of the observation (float object).
        """
        self._observations[state] = time

    def make_observation_check_timestamp(self, state: CellState, time: float) -> None:
        """
        Record an observation for the grid cell, without overwriting a newer timestamp.

        Args:
            state: The observed CellState.
            time: The time of the observation (float object).
        """
        prev_timestamp = self._observations[state]
        self._observations[state] = max(time, prev_timestamp)

    def current_state(self, current_time: float) -> tuple[CellState, float]:
        """
        Calculate the current state of the cell using observations and exponential decay.

        Args:
            current_time: Current time (float object).

        Returns:
            Tuple (most_likely_state, certainty) where the state is the most probable and
            certainty is the confidence.
        """
        if not self._observations:
            return CellState.UNKNOWN, 1.0

        decay_constants = np.array([0.0, 0.2, 0.05, 0.08])  # Indexed by CellState Enum values

        # Prepare arrays for Numba-compatible computation
        states = []
        elapsed_times = []
        for state, timestamp in self._observations.items():
            states.append(state.value)  # Store enum value as an integer
            elapsed_times.append(current_time - timestamp)

        # Convert to NumPy arrays for Numba computation
        states = np.array(states)
        elapsed_times = np.array(elapsed_times)

        # Use the Numba-optimized certainty computation
        most_likely_state_val, certainty = compute_certainty_numba(states, elapsed_times, decay_constants)
        return CellState(most_likely_state_val), certainty
