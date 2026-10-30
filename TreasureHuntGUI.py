import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from PIL import Image, ImageTk
from search import bfs_steps, dfs_steps, ucs_steps
from TreasureGridModel import MyGridModel, EMPTY, START, STATIC_WALL, TREASURE, TRAP


class TreasureHuntGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Treasure Hunt Game")

        # Top bar with the hamburger menu button that opens Custom Grid Setup
        self.topbar = tk.Frame(self.root)
        self.topbar.pack(fill="x", padx=10, pady=(10, 0))

        self.menu_button = tk.Button(
            self.topbar,
            text="☰",  # hamburger icon (three bars)
            font=("Arial", 14),
            width=3,
            command=self.open_settings_menu
        )
        self.menu_button.pack(side=tk.LEFT)

        # Reference to the settings window, so clicking the menu button
        # twice doesn't open duplicate windows
        self.settings_window = None

        # Gets the grid
        self.model = MyGridModel(10)
        # Set the agent's starting position
        self.start = self.model.start
        # Store the path found by a search algorithm
        self.path = None
        # Cells visited so far during an in-progress animated search
        self.visited_cells = []
        # Delay between animation steps, in milliseconds
        self.animation_delay_ms = 80
        # The generator currently driving a running search animation, if any
        self._search_generator = None
        # Set grid cell size
        self.cell_size = 60

        # load the image
        image_path = Path(__file__).parent / "images" / "chess_guy.png"
        image = Image.open(image_path)
        image = image.resize((self.cell_size, self.cell_size), Image.Resampling.LANCZOS)
        self.agent_image = ImageTk.PhotoImage(image)

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
            command=lambda: self.run_search(bfs_steps, "BFS")
        )
        self.bfs_button.pack(side=tk.LEFT, padx=5)

        self.dfs_button = tk.Button(
            self.button_frame,
            text="Run DFS",
            command=lambda: self.run_search(dfs_steps, "DFS")
        )
        self.dfs_button.pack(side=tk.LEFT, padx=5)

        self.ucs_button = tk.Button(
            self.button_frame,
            text="Run UCS",
            command=lambda: self.run_search(ucs_steps, "UCS")
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

    def open_settings_menu(self):
        # If the settings window is already open, just bring it to front
        # instead of creating a second one
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Custom Grid Setup")
        self.settings_window.resizable(False, False)
        # Keep it in front of the main window, but not block interacting with it
        self.settings_window.transient(self.root)

        def labeled_entry(row, label_text, default_value, width=20):
            tk.Label(self.settings_window, text=label_text).grid(
                row=row, column=0, sticky="w", padx=10, pady=5
            )
            entry = tk.Entry(self.settings_window, width=width)
            entry.insert(0, default_value)
            entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
            return entry

        self.size_entry = labeled_entry(0, "Grid Size (N):", str(self.model.size), width=6)
        self.start_entry = labeled_entry(1, "Start (row,col):", "0,0")
        self.treasure_entry = labeled_entry(2, "Treasure (row,col):", "5,5")
        self.traps_entry = labeled_entry(3, "Traps (row,col; row,col; ...):", "3,3; 4,4")
        self.walls_entry = labeled_entry(4, "Walls (row,col; row,col; ...):", "1,1; 1,2; 2,2")

        self.apply_button = tk.Button(
            self.settings_window,
            text="Apply Custom Grid",
            command=self.apply_custom_grid
        )
        self.apply_button.grid(row=5, column=0, columnspan=2, pady=(5, 10))

    def _parse_coord(self, text, label):
        try:
            row_str, col_str = text.split(",")
            return (int(row_str.strip()), int(col_str.strip()))
        except (ValueError, AttributeError):
            raise ValueError(f"{label} must look like 'row,col', got: {text!r}")

    def _parse_coord_list(self, text, label):
        text = text.strip()
        if not text:
            return []
        return [self._parse_coord(part, label) for part in text.split(";") if part.strip()]

    def apply_custom_grid(self):
        try:
            size = int(self.size_entry.get().strip())
            if size < 8:
                raise ValueError("Grid size (N) must be at least 8")

            start = self._parse_coord(self.start_entry.get(), "Start")
            treasure = self._parse_coord(self.treasure_entry.get(), "Treasure")
            traps = self._parse_coord_list(self.traps_entry.get(), "Trap")
            walls = self._parse_coord_list(self.walls_entry.get(), "Wall")

            self.model.set_custom_grid(size, start, treasure, traps, walls)
        except ValueError as error:
            messagebox.showerror("Invalid Grid Setup", str(error))
            return

        # Resize canvas in case grid size changed
        self.canvas.config(
            width=self.model.size * self.cell_size,
            height=self.model.size * self.cell_size
        )

        self.start = self.model.start
        self.path = None
        self.visited_cells = []
        self.stats_label.config(text="Select an algorithm to begin.")
        self.draw_grid()

        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.destroy()

    def regenerate_grid(self):
        self.model.generate_grid()
        # Clear the previous search path and visited-cell highlights
        self.path = None
        self.visited_cells = []

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

                # Color cells the search has visited so far, while it's animating
                if color == "white" and (row, col) in self.visited_cells:
                    color = "lightblue"

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

                # for drawing the start image
                if (row, col) == self.start:
                    self.canvas.create_image(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        image=self.agent_image
                    )


    def _set_controls_state(self, state):
        self.bfs_button.config(state=state)
        self.dfs_button.config(state=state)
        self.ucs_button.config(state=state)
        self.regenerate_button.config(state=state)
        self.menu_button.config(state=state)

    def run_search(self, algorithm_steps, algorithm_name):
        # Get the treasure's position from the grid model
        goal = self.model.treasure_position

        # Reset any previous search's visuals
        self.path = None
        self.visited_cells = []

        # Lock out other actions while the animation is running
        self._set_controls_state(tk.DISABLED)
        self.stats_label.config(text=f"Running {algorithm_name}...")

        self._search_generator = algorithm_steps(self.model.grid, self.start, goal)
        self._animate_search_step(algorithm_name)

    def _animate_search_step(self, algorithm_name):
        try:
            current = next(self._search_generator)
        except StopIteration as finished:
            path, nodes_expanded, runtime = finished.value
            self._finish_search(algorithm_name, path, nodes_expanded, runtime)
            return

        # Mark this cell as visited, unless it's the start or treasure
        # (those already have their own fixed appearance)
        if current != self.start and current != self.model.treasure_position:
            self.visited_cells.append(current)

        self.draw_grid()

        self.root.after(
            self.animation_delay_ms,
            lambda: self._animate_search_step(algorithm_name)
        )

    def _finish_search(self, algorithm_name, path, nodes_expanded, runtime):
        # Store the path so the GUI can highlight it
        self.path = path
        self.draw_grid()

        # Print results
        print("Path:", path)
        print("Path cost:", len(path) - 1 if path else "No path found")
        print("Nodes expanded:", nodes_expanded)
        print("Runtime:", runtime)

        # statistics displayed on GUI
        path_length = len(path) - 1 if path else "No path found"

        self.stats_label.config(
            text=f"{algorithm_name} finished\n"
                f"Path cost: {path_length}\n"
                f"Nodes Expanded: {nodes_expanded}\n"
                f"Execution Time: {runtime:.6f} seconds"
        )

        self._set_controls_state(tk.NORMAL)



if __name__ == "__main__":
    root = tk.Tk()
    app = TreasureHuntGUI(root)
    root.mainloop()