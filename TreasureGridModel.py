import random
import numpy as np


# Cell type constants
EMPTY = 0
START = 1
STATIC_WALL = 2
TREASURE = 3
TRAP = 4

class MyGridModel:
    def __init__(self, n=8):
        self.size = n

        self.start = None
        self.treasure_position = None
        self.trap_position = None

        self.wall_positions = set()
        self.grid = np.zeros((self.size, self.size), dtype=int)
        self.generate_grid()

    def generate_grid(self):
        generate_random_2d_int_coordinate \
            = lambda: (random.randint(0, self.size - 1), random.randint(0, self.size - 1))

        self.grid = np.zeros((self.size, self.size), dtype=int)
        self.wall_positions = set()

        # place start position.
        # fixed to (0, 0).
        self.start = (0, 0)
        x, y = self.start
        self.grid[x, y] = START

        # place treasure position on grid
        self.treasure_position = generate_random_2d_int_coordinate()
        x, y = self.treasure_position

        if self.grid[x, y] == EMPTY:
            self.grid[x, y] = TREASURE
        else: # keep looking for empty position in grid to place treasure
            while self.grid[x, y] != EMPTY:
                x, y = generate_random_2d_int_coordinate()
            self.grid[x, y] = TREASURE
            self.treasure_position = (x, y)

        # place trap position on grid
        self.trap_position = generate_random_2d_int_coordinate()
        x, y = self.trap_position

        if self.grid[x, y] == EMPTY:
            self.grid[x, y] = TRAP
        else: # keep looking for empty position in grid to place trap
            while self.grid[x, y] != EMPTY:
                x, y = generate_random_2d_int_coordinate()
            self.grid[x, y] = TRAP
            self.trap_position = (x, y)

        # place static wall positions on grid
        static_wall_amount = self.size // 2 # amount of static walls is half of linear spaces n using integer division
        for i in range(static_wall_amount):
            x, y = generate_random_2d_int_coordinate()

            if self.grid[x, y] == EMPTY:
                self.grid[x, y] = STATIC_WALL
                self.wall_positions.add((x, y))
            else:
                x, y = generate_random_2d_int_coordinate()
                while self.grid[x, y] != EMPTY:
                    x, y = generate_random_2d_int_coordinate()
                self.grid[x, y] = STATIC_WALL
                self.wall_positions.add((x, y))


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

    def set_custom_grid(self, size, start, treasure, traps, walls):
        """
        Build the grid from explicit (row, col) positions instead of random
        placement, for demo/presentation setups. `traps` and `walls` are
        lists of (row, col) tuples. Raises ValueError if any position is
        out of bounds or overlaps another.
        """
        labeled_positions = [("start", start), ("treasure", treasure)]
        labeled_positions += [("trap", pos) for pos in traps]
        labeled_positions += [("wall", pos) for pos in walls]
        
        seen = {}
        for label, (row, col) in labeled_positions:
            if not (0 <= row < size and 0 <= col < size):
                raise ValueError(f"{label} position {row, col} is outside the {size}x{size} grid")
            if (row, col) in seen:
                raise ValueError(f"{label} position {(row, col)} overlaps with {seen[(row, col)]}")
            seen[(row, col)] = label
        
        self.size = size
        self.grid = np.zeros((self.size, self.size), dtype=int)
        self.wall_positions = set()
        
        self.start = start
        self.treasure_position = treasure
        self.trap_positions = list(traps)
        self.trap_position = traps[0] if traps else None # Kept for backward compatibility
        
        row, col = start
        self.grid[row, col] = START
        
        row, col = treasure
        self.grid[row, col] = TREASURE
        
        for row, col in traps:
            self.grid[row, col] = TRAP
            
        for row, col in walls:
            self.grid[row, col] = STATIC_WALL
            self.wall_positions.add((row, col))