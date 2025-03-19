import pickle
from collections import defaultdict
from .grid_cell import GridCell

class OccupancyGrid:
    GRID_CELL_SIZE_MM: int = 500

    def __init__(self) -> None:
        """Initialize a grid with cells managed as a dictionary."""
        self._cells: defaultdict[tuple[int, int], GridCell] = defaultdict(GridCell)

    def get_cell(self, x: int, y: int) -> GridCell:
        """Access a specific grid cell by coordinates."""
        return self._cells[(x, y)]

    def to_bytes(self) -> bytes:
        """ Convert the grid to bytes, so it can be sent over the network. """
        return pickle.dumps(dict(self._cells))

    def update_from_bytes(self, data: bytes, check_timestamp: bool = False) -> None:
        """ Update the grid from bytes received over the network. """
        received_cells = pickle.loads(data)
        if check_timestamp:
            for coords, new_cell in received_cells.items():
                current_cell = self._cells[coords]
                for state, timestamp in new_cell._observations.items():
                    current_cell.make_observation(state, timestamp)
        else:
            for coords, new_cell in received_cells.items():
                current_cell = self._cells[coords]
                for state, timestamp in new_cell._observations.items():
                    current_cell.make_observation_check_timestamp(state, timestamp)

