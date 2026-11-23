"""Grid model for the Treasure Hunt project.

Cell encodings are shared by the GUI and search modules. Random generation
uses a 15x15 grid by default, with a fixed start at (0, 0), 3-5 treasures,
2-3 traps, and several walls. Older assignments may instantiate other sizes;
random generation scales object counts sensibly for those sizes.

The grid generation and custom-grid validation below use ordinary loops rather
than list comprehensions, to make the steps easier to follow.
"""
import random
import numpy as np

EMPTY, START, STATIC_WALL, TREASURE, TRAP = 0, 1, 2, 3, 4


class MyGridModel:
    def __init__(self, n=15):
        self.size = n
        self.start = None
        self.treasure_position = None
        self.trap_position = None
        self.wall_positions = set()
        self.grid = np.zeros((n, n), dtype=int)
        self.generate_grid()

    def generate_grid(self):
        """Generate a random, non-overlapping grid with bounded placement."""
        n = self.size
        if n < 5:
            raise ValueError("Grid size must be at least 5")

        self.grid = np.zeros((n, n), dtype=int)
        self.wall_positions = set()
        self.start = (0, 0)
        self.grid[self.start] = START

        # Build a list of available coordinates, excluding the start.
        available = []
        row = 0
        while row < n:
            col = 0
            while col < n:
                position = (row, col)
                if position != self.start:
                    available.append(position)
                col += 1
            row += 1

        # Shuffle the coordinates so object locations are random.
        random.shuffle(available)

        # Choose object counts. Larger Assignment 3 grids use the required
        # treasure/trap ranges; smaller legacy grids use reduced counts.
        if n >= 15:
            treasure_count = random.randint(3, 5)
            trap_count = random.randint(2, 3)
        else:
            treasure_count = random.randint(2, min(3, n - 2))
            trap_count = 2

        wall_count = max(n // 2, int(n * n * 0.08))

        if treasure_count > len(available):
            treasure_count = len(available)

        treasures = []
        count = 0
        while count < treasure_count:
            treasures.append(available.pop())
            count += 1

        traps = []
        count = 0
        while count < trap_count and len(available) > 0:
            traps.append(available.pop())
            count += 1

        walls = []
        count = 0
        while count < wall_count and len(available) > 0:
            walls.append(available.pop())
            count += 1

        self.treasure_positions = treasures
        self.trap_positions = traps
        self.treasure_position = treasures[0] if len(treasures) > 0 else None
        self.trap_position = traps[0] if len(traps) > 0 else None

        # Place the objects on the grid and track wall coordinates.
        for position in treasures:
            self.grid[position] = TREASURE

        for position in traps:
            self.grid[position] = TRAP

        for position in walls:
            self.grid[position] = STATIC_WALL
            self.wall_positions.add(position)

    def is_static_wall(self, x, y):
        return self.grid[x, y] == STATIC_WALL

    def is_trap(self, x, y):
        return self.grid[x, y] == TRAP

    def is_empty(self, x, y):
        return self.grid[x, y] == EMPTY

    def is_treasure(self, x, y):
        return self.grid[x, y] == TREASURE

    def get_cell(self, x, y):
        return int(self.grid[x, y])

    def grid_copy(self):
        return self.grid.copy()

    def set_custom_grid(self, size, start, treasures, traps, walls):
        """Apply a custom layout after checking bounds and overlap consistency."""
        if size < 5:
            raise ValueError("Grid size must be at least 5")
        if not treasures:
            raise ValueError("At least one treasure is required")

        # Collect labeled coordinates using loops, so each validation step is
        # visible and straightforward to follow.
        labeled_positions = []
        labeled_positions.append(("start", start))

        for position in treasures:
            labeled_positions.append(("treasure", position))

        for position in traps:
            labeled_positions.append(("trap", position))

        for position in walls:
            labeled_positions.append(("wall", position))

        # Check that every coordinate is valid and that no two objects overlap.
        seen = {}
        for label, position in labeled_positions:
            if not isinstance(position, (tuple, list)) or len(position) != 2:
                raise ValueError(f"Invalid {label} coordinate: {position}")

            row, col = position
            if not (0 <= row < size and 0 <= col < size):
                raise ValueError(
                    f"{label} position {position} is outside the {size}x{size} grid"
                )

            coordinate = (row, col)
            if coordinate in seen:
                raise ValueError(
                    f"{label} position {position} overlaps with {seen[coordinate]}"
                )
            seen[coordinate] = label

        # Only replace the existing model after the custom layout passes checks.
        self.size = size
        self.grid = np.zeros((size, size), dtype=int)
        self.wall_positions = set()
        self.start = tuple(start)

        self.treasure_positions = []
        for position in treasures:
            self.treasure_positions.append(tuple(position))
        self.treasure_position = self.treasure_positions[0]

        self.trap_positions = []
        for position in traps:
            self.trap_positions.append(tuple(position))
        if len(self.trap_positions) > 0:
            self.trap_position = self.trap_positions[0]
        else:
            self.trap_position = None

        self.grid[self.start] = START

        for position in self.treasure_positions:
            self.grid[position] = TREASURE

        for position in self.trap_positions:
            self.grid[position] = TRAP

        for position in walls:
            coordinate = tuple(position)
            self.grid[coordinate] = STATIC_WALL
            self.wall_positions.add(coordinate)
