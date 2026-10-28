import tkinter as tk
from search import bfs, dfs, ucs
from TreasureGridModel import MyGridModel, EMPTY, STATIC_WALL, TREASURE, TRAP


class TreasureHuntGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Treasure Hunt Game")

        # Gets the grid
        self.model = MyGridModel(10)
        # Set the agent's starting position
        self.start = (0, 0)
        # Store the path found by a search algorithm
        self.path = None
        # Set grid cell size
        self.cell_size = 60

        # Create a canvas to display the grid
        self.canvas = tk.Canvas(
            self.root,
            width=self.model.size * self.cell_size,
            height=self.model.size * self.cell_size,
            bg="white"
        )
        self.canvas.pack(padx=20, pady=20)

        # Create buttons for each search algorithm
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=10)

        self.bfs_button = tk.Button(
            self.button_frame,
            text="Run BFS",
            command=lambda: self.run_search(bfs)
)
        self.bfs_button.pack(side=tk.LEFT, padx=5)

        self.dfs_button = tk.Button(
            self.button_frame,
            text="Run DFS",
            command=lambda: self.run_search(dfs)
)
        self.dfs_button.pack(side=tk.LEFT, padx=5)

        self.ucs_button = tk.Button(
            self.button_frame,
            text="Run UCS",
            command=lambda: self.run_search(ucs)
)
        self.ucs_button.pack(side=tk.LEFT, padx=5)
        # Display search algorithm statistics
        self.stats_label = tk.Label(
            self.root,
            text="Select an algorithm to begin.",
            font=("Arial", 12),
            justify="left"
)
        self.stats_label.pack(pady=10)

        # Button to regenerate the grid
        self.regenerate_button = tk.Button(
            self.root,
            text="Regenerate Grid",
            command=self.regenerate_grid
        )
        self.regenerate_button.pack(pady=(0, 20))

        # Draw the grid
        self.draw_grid()

    def regenerate_grid(self):
        self.model.generate_grid()
        # Clear the previous search path
        self.path = None

        # Reset the statistics display
        self.stats_label.config(
        text="Select an algorithm to begin."
        )

        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")

        for row in range(self.model.size):
            for col in range(self.model.size):
                cell = self.model.grid[row, col]

                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "white"
                symbol = ""

                if cell == STATIC_WALL:
                    color = "gray"
                    symbol = "#"
                elif cell == TREASURE:
                    color = "lightgreen"
                    symbol = "T"
                elif cell == TRAP:
                    color = "lightcoral"
                    symbol = "X"

                    # Should highlight the path without covering walls or treasure
                if self.path and (row, col) in self.path:
                    if (row, col) != self.start and (row, col) != self.model.treasure_position:
                        color = "yellow"

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline="black"
                )

                if symbol:
                    self.canvas.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text=symbol,
                        font=("Arial", 20, "bold")
                    )


    def run_search(self, algorithm):
        # Get the treasure's position from the grid model
        goal = self.model.treasure_position

        # Run the selected search algorithm
        path, nodes_expanded, runtime = algorithm(
            self.model.grid, self.start, goal
        )

        # Store the path so the GUI can highlight it
        self.path = path

        # Redraw the grid with the search result
        self.draw_grid()

        # Print results
        print("Path:", path)
        print("Path length:", len(path) - 1 if path else "No path found")
        print("Nodes expanded:", nodes_expanded)
        print("Runtime:", runtime)

        # statistics displayed on GUI
        path_length = len(path) - 1 if path else "No path found"

        self.stats_label.config(
            text=f"Path Length: {path_length}\n"
                f"Nodes Expanded: {nodes_expanded}\n"
                f"Execution Time: {runtime:.6f} seconds"
)



if __name__ == "__main__":
    root = tk.Tk()
    app = TreasureHuntGUI(root)
    root.mainloop()
