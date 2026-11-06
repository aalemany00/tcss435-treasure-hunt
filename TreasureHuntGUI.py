import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from PIL import Image, ImageTk
from search import bfs_steps, dfs_steps, ucs_steps, greedy_best_first_steps, compute_path_cost, count_traps_triggered
from heuristics import manhattan_distance, closest_treasure
from TreasureGridModel import MyGridModel, EMPTY, START, STATIC_WALL, TREASURE, TRAP


class TreasureHuntGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Treasure Hunt Game")

        # Top bar with the hamburger menu button that opens Custom Grid Setup
        self.topbar = tk.Frame(self.root)
        self.topbar.pack(side=tk.TOP, fill="x", padx=10, pady=(10, 0))

        self.menu_button = tk.Button(
            self.topbar,
            text="☰",
            font=("Arial", 14),
            width=3,
            command=self.open_settings_menu
        )
        self.menu_button.pack(side=tk.LEFT)

        self.settings_window = None

        self.model = MyGridModel(10)
        self.start = self.model.start
        self.path = None
        self.visited_cells = []
        self.animation_delay_ms = 80
        self._search_generator = None

        image_path = Path(__file__).parent / "images" / "chess_guy.png"
        self.agent_original_image = Image.open(image_path)
        self.update_cell_size()

        # --- Bottom controls are built and packed FIRST, to the bottom, so
        # they always keep their space no matter how big the grid or how many
        # lines the stats label needs. The grid canvas (which has its own
        # scrollbars) gets whatever space is left over. ---

        self.button_frame = tk.Frame(self.root)
        self.bfs_button = tk.Button(self.button_frame, text="Run BFS", command=lambda: self.run_search(bfs_steps, "BFS"))
        self.bfs_button.pack(side=tk.LEFT, padx=5)
        self.dfs_button = tk.Button(self.button_frame, text="Run DFS", command=lambda: self.run_search(dfs_steps, "DFS"))
        self.dfs_button.pack(side=tk.LEFT, padx=5)
        self.ucs_button = tk.Button(self.button_frame, text="Run UCS", command=lambda: self.run_search(ucs_steps, "UCS"))
        self.ucs_button.pack(side=tk.LEFT, padx=5)
        self.greedy_button = tk.Button(self.button_frame, text="Run Greedy", command=self.run_greedy_search)
        self.greedy_button.pack(side=tk.LEFT, padx=5)

        self.regenerate_button = tk.Button(self.root, text="Regenerate Grid", command=self.regenerate_grid)
        self.regenerate_button.pack(side=tk.BOTTOM, pady=(0, 15))

        self.stats_label = tk.Label(
            self.root,
            text="Select an algorithm to begin.",
            font=("Arial", 12),
            justify="left"
        )
        self.stats_label.pack(side=tk.BOTTOM, pady=10)

        self.button_frame.pack(side=tk.BOTTOM, pady=10)

        # --- Grid canvas: packed LAST, so it fills whatever space is left ---

        self.grid_frame = tk.Frame(self.root)
        self.grid_frame.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=True)

        viewport_width = min(800, self.root.winfo_screenwidth() - 80)
        viewport_height = min(650, self.root.winfo_screenheight() - 300)

        self.horizontal_scrollbar = tk.Scrollbar(self.grid_frame, orient=tk.HORIZONTAL)
        self.vertical_scrollbar = tk.Scrollbar(self.grid_frame, orient=tk.VERTICAL)

        self.canvas = tk.Canvas(
            self.grid_frame,
            width=viewport_width,
            height=viewport_height,
            bg="white",
            xscrollcommand=self.horizontal_scrollbar.set,
            yscrollcommand=self.vertical_scrollbar.set
        )

        self.horizontal_scrollbar.config(command=self.canvas.xview)
        self.vertical_scrollbar.config(command=self.canvas.yview)

        self.horizontal_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.vertical_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Safety net: never let the window grow taller than the screen
        self.root.update_idletasks()
        max_height = self.root.winfo_screenheight() - 80
        if self.root.winfo_reqheight() > max_height:
            self.root.geometry(f"{self.root.winfo_reqwidth()}x{max_height}")

        self.draw_grid()

    def update_cell_size(self):
        if self.model.size <= 10:
            self.cell_size = 60
        elif self.model.size <= 20:
            self.cell_size = 40
        elif self.model.size <= 50:
            self.cell_size = 30
        else:
            self.cell_size = 20

        image = self.agent_original_image.resize(
            (self.cell_size, self.cell_size),
            Image.Resampling.LANCZOS
        )
        self.agent_image = ImageTk.PhotoImage(image)

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
        self.start_entry = labeled_entry(1, "Start (row,col):", self._format_coord(self.model.start))
        self.treasure_entry = labeled_entry(2, "Treasures (row,col; row,col; ...):", self._format_coord_list(self._get_treasure_positions()))
        self.traps_entry = labeled_entry(3, "Traps (row,col; row,col; ...):", self._format_coord_list(self._get_trap_positions()))
        self.walls_entry = labeled_entry(4, "Walls (row,col; row,col; ...):", self._format_coord_list(sorted(self.model.wall_positions)))

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
            treasures = self._parse_coord_list(self.treasure_entry.get(), "Treasure")
            traps = self._parse_coord_list(self.traps_entry.get(), "Trap")
            walls = self._parse_coord_list(self.walls_entry.get(), "Wall")

            self.model.set_custom_grid(size, start, treasures, traps, walls)
        except ValueError as error:
            messagebox.showerror("Invalid Grid Setup", str(error))
            return

        self.start = self.model.start
        self.path = None
        self.visited_cells = []

        # Adjust cell size for the newly selected grid
        self.update_cell_size()

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
                    if (row, col) != self.start and cell != TREASURE and cell != TRAP:
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
                        #font=("Arial", 20, "bold")
                        font=("Arial", max(10, self.cell_size // 2), "bold")
                    )

                # for drawing the start image
                if (row, col) == self.start:
                    self.canvas.create_image(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        image=self.agent_image
                    )

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    def _set_controls_state(self, state):
        self.bfs_button.config(state=state)
        self.dfs_button.config(state=state)
        self.ucs_button.config(state=state)
        self.greedy_button.config(state=state)   
        self.regenerate_button.config(state=state)
        self.menu_button.config(state=state)

    def run_search(self, algorithm_steps, algorithm_name):
        goal = closest_treasure(self.start, self._get_treasure_positions())

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
        if current != self.start and current not in self._get_treasure_positions():
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

        # statistics displayed on GUI
        if path:
            path_cost = compute_path_cost(self.model.grid, path)
            traps_triggered = count_traps_triggered(self.model.grid, path)
        else:
            path_cost = "No path found"
            traps_triggered = 0

        # Print results
        print("Path:", path)
        print("Path cost:", path_cost)
        print("Nodes expanded:", nodes_expanded)
        print("Runtime:", runtime)

        self.stats_label.config(
            text=f"{algorithm_name} finished\n"
                f"Path cost: {path_cost}\n"
                f"Nodes Expanded: {nodes_expanded}\n"
                f"Execution Time: {runtime:.6f} seconds\n"
                f"Traps Triggered: {traps_triggered}"
        )

        self._set_controls_state(tk.NORMAL)
        
    def _get_treasure_positions(self):
        # Supports both today's single-treasure model and an updated
        # multi-treasure model (treasure_positions list), once the grid
        # setup gets updated for 2-3 treasures.
        if hasattr(self.model, "treasure_positions") and self.model.treasure_positions:
            return list(self.model.treasure_positions)
        return [self.model.treasure_position]

    def _format_coord(self, coord):
        return f"{coord[0]},{coord[1]}"

    def _format_coord_list(self, coords):
        return "; ".join(self._format_coord(c) for c in coords)

    def _get_trap_positions(self):
        # Supports both today's single-trap model and a model updated to
        # track multiple traps (trap_positions list).
        if hasattr(self.model, "trap_positions") and self.model.trap_positions:
            return list(self.model.trap_positions)
        if self.model.trap_position is not None:
            return [self.model.trap_position]
        return []

    def run_greedy_search(self):
        treasures = self._get_treasure_positions()
        goal = closest_treasure(self.start, treasures)

        self.path = None
        self.visited_cells = []
        self._heuristic_log = {}
        self._greedy_goal = goal

        self._set_controls_state(tk.DISABLED)
        self.stats_label.config(text="Running Greedy Best-First Search...")

        self._search_generator = greedy_best_first_steps(
            self.model.grid, self.start, goal,
            heuristic=manhattan_distance,
            heuristic_log=self._heuristic_log
        )
        self._animate_greedy_step()

    def _animate_greedy_step(self):
        try:
            current = next(self._search_generator)
        except StopIteration as finished:
            path, nodes_expanded, runtime = finished.value
            self._finish_greedy_search(path, nodes_expanded, runtime)
            return

        if current != self.start and current not in self._get_treasure_positions():
            self.visited_cells.append(current)

        self.draw_grid()
        self.root.after(self.animation_delay_ms, self._animate_greedy_step)

    def _finish_greedy_search(self, path, nodes_expanded, runtime):
        self.path = path
        self.draw_grid()

        if path:
            path_cost = compute_path_cost(self.model.grid, path)
            traps_triggered = count_traps_triggered(self.model.grid, path)
        else:
            path_cost = "No path found"
            traps_triggered = 0

        start_heuristic = self._heuristic_log.get(
            self.start, manhattan_distance(self.start, self._greedy_goal)
        )

        print("Path:", path)
        print("Path cost:", path_cost)
        print("Nodes expanded:", nodes_expanded)
        print("Runtime:", runtime)
        print("Heuristic values computed:", self._heuristic_log)

        self.stats_label.config(
            text=f"Greedy Best-First Search finished\n"
                f"Goal treasure: {self._greedy_goal}\n"
                f"Path cost: {path_cost}\n"
                f"Nodes Expanded: {nodes_expanded}\n"
                f"Execution Time: {runtime:.6f} seconds\n"
                f"Traps Triggered: {traps_triggered}\n"
                f"Start heuristic (Manhattan to goal): {start_heuristic}\n"
                f"Heuristic values computed: {len(self._heuristic_log)}"
        )

        self._set_controls_state(tk.NORMAL)



if __name__ == "__main__":
    root = tk.Tk()
    app = TreasureHuntGUI(root)
    root.mainloop()