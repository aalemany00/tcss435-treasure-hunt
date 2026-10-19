import random
import numpy as np


# Cell type constants
EMPTY = 0
STATIC_WALL = 1
TREASURE = 2
TRAP = 3

class MyGridModel:
    def __init__(self, n=8):
        self.size = n

        self.treasure_position = None
        self.trap_position = None
        self.wall_positions = set()
        self.grid = np.zeros((self.size, self.size), dtype=int)
        self.generate_grid()

    def generate_grid(self):
        """
        for row in range(self.size):
            for column in range(self.size):
                self.grid[row, column] = column
        """
        generate_random_2d_int_coordinate \
            = lambda: (random.randint(0, self.size - 1), random.randint(0, self.size - 1))

        self.grid = np.zeros((self.size, self.size), dtype=int)
        self.wall_positions = set()

        # place treasure position on grid
        # initially grid is all zeros so should be
        # safe to randomly generate 2d coord without checking if EMPTY
        self.treasure_position = generate_random_2d_int_coordinate()
        x, y = self.treasure_position
        self.grid[x, y] = TREASURE

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


        # test generate_grid for later
        #print(self.grid)

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
