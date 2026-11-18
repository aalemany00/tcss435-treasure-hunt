import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from PIL import Image, ImageTk
from search import bfs_steps, dfs_steps, ucs_steps, greedy_best_first_steps, a_star_steps, compute_path_cost, count_traps_triggered
from adversarial import GameState, minimax, alpha_beta, play_game
from heuristics import manhattan_distance, euclidean_distance
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

        self.model = MyGridModel(20)
        self.start = self.model.start
        self.path = None
        self.visited_cells = []
        self.animation_delay_ms = 10
        self.animation_steps_per_tick = 5
        self._search_generator = None
        
        self.game_state = None

        image_path = Path(__file__).parent / "images" / "chess_guy.png"
        self.agent_original_image = Image.open(image_path)
        self.update_cell_size()

        # --- Bottom controls are built and packed FIRST, to the bottom, so
        # they always keep their space no matter how big the grid or how many
        # lines the stats label needs. The grid canvas (which has its own
        # scrollbars) gets whatever space is left over. ---

        self.button_frame = tk.Frame(self.root)
        
        self.algorithm_options = [
            "BFS", "DFS", "UCS", "Greedy",
            "A* (Manhattan)", "A* (Euclidean)",
            "Minimax", "Alpha-Beta",
        ]
        self.algorithm_var = tk.StringVar(value=self.algorithm_options[0])
        self.algorithm_menu = tk.OptionMenu(self.button_frame, self.algorithm_var, *self.algorithm_options)
        self.algorithm_menu.config(width=16)
        self.algorithm_menu.pack(side=tk.LEFT, padx=5)

        self.run_button = tk.Button(self.button_frame, text="Run", command=self.run_selected_algorithm)
        self.run_button.pack(side=tk.LEFT, padx=5)

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
        
        self.depth_label = tk.Label(self.button_frame, text="Depth:")
        self.depth_label.pack(side=tk.LEFT, padx=(15, 2))

        self.depth_entry = tk.Entry(self.button_frame, width=4)
        self.depth_entry.insert(0, "4")
        self.depth_entry.pack(side=tk.LEFT, padx=2)

        self.minimax_button = tk.Button(
            self.button_frame, text="Run Minimax",
            command=lambda: self.run_adversarial(minimax, "Minimax")
        )
        self.minimax_button.pack(side=tk.LEFT, padx=5)

        self.alpha_beta_button = tk.Button(
            self.button_frame, text="Run Alpha-Beta",
            command=lambda: self.run_adversarial(alpha_beta, "Alpha-Beta")
        )
        self.alpha_beta_button.pack(side=tk.LEFT, padx=5)

        # --- Grid canvas: packed LAST, so it fills whatever space is left ---

        self.grid_frame = tk.Frame(self.root)
        self.grid_frame.pack(side=tk.TOP, padx=10, pady=10)

        self.canvas = tk.Canvas(
            self.grid_frame,
            width=self.cell_size * self.model.size,
            height=self.cell_size * self.model.size,
            bg="white"
        )
        self.canvas.pack()

        # Safety net: never let the window grow taller than the screen
        self.root.update_idletasks()
        max_height = self.root.winfo_screenheight() - 80
        if self.root.winfo_reqheight() > max_height:
            self.root.geometry(f"{self.root.winfo_reqwidth()}x{max_height}")

        self.draw_grid()

    def update_cell_size(self):
        max_width = min(900, self.root.winfo_screenwidth() - 100)
        max_height = min(650, self.root.winfo_screenheight() - 300)
        size = max(1, self.model.size)
        self.cell_size = max(4, min(max_width // size, max_height // size))

        image = self.agent_original_image.resize(
            (self.cell_size, self.cell_size),
            Image.Resampling.LANCZOS
        )
        self.agent_image = ImageTk.PhotoImage(image)

        if hasattr(self, "canvas"):
            self.canvas.config(
                width=self.cell_size * self.model.size,
                height=self.cell_size * self.model.size
            )

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
        self.start = self.model.start
        self.path = None
        self.visited_cells = []
        self.game_state = None

        # Adjust cell size for the newly selected grid
        self.update_cell_size()

        self.stats_label.config(text="Select an algorithm to begin.")
        self.draw_grid()

        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.destroy()

    def regenerate_grid(self):
        self.model.generate_grid()
        # Clear the previous search path, visited-cell highlights, and any
        # adversarial game in progress -- agents shouldn't linger on a new grid
        self.path = None
        self.visited_cells = []
        self.game_state = None

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
                elif cell == TREASURE and (self.game_state is None or (row, col) 
                                           in self.game_state.treasures):
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
                
                if self.game_state is not None:
                    if (row, col) == self.game_state.agent_a_pos:
                        self.canvas.create_oval(x1 + 5, y1 + 5, x2 - 5, y2 - 5, fill="blue")
                        self.canvas.create_text(
                            (x1 + x2) / 2, (y1 + y2) / 2, text="A", fill="white",
                            font=("Arial", max(10, self.cell_size // 2), "bold")
                        )
                    if (row, col) == self.game_state.agent_b_pos:
                        self.canvas.create_oval(x1 + 5, y1 + 5, x2 - 5, y2 - 5, fill="purple")
                        self.canvas.create_text(
                            (x1 + x2) / 2, (y1 + y2) / 2, text="B", fill="white",
                            font=("Arial", max(10, self.cell_size // 2), "bold")
                        )


    def _set_controls_state(self, state):
        self.algorithm_menu.config(state=state)
        self.run_button.config(state=state)
        self.depth_entry.config(state=state)
        self.regenerate_button.config(state=state)
        self.menu_button.config(state=state)


    def run_selected_algorithm(self):
        choice = self.algorithm_var.get()
        dispatch = {
            "BFS": lambda: self.run_search(bfs_steps, "BFS"),
            "DFS": lambda: self.run_search(dfs_steps, "DFS"),
            "UCS": lambda: self.run_search(ucs_steps, "UCS"),
            "Greedy": self.run_greedy_search,
            "A* (Manhattan)": lambda: self.run_astar_search(manhattan_distance, "Manhattan"),
            "A* (Euclidean)": lambda: self.run_astar_search(euclidean_distance, "Euclidean"),
            "Minimax": lambda: self.run_adversarial(minimax, "Minimax"),
            "Alpha-Beta": lambda: self.run_adversarial(alpha_beta, "Alpha-Beta"),
        }
        dispatch[choice]()
    

    def run_search(self, algorithm_steps, algorithm_name):
        goal = self._get_treasure_positions()

        # Reset any previous search's visuals
        self.path = None
        self.visited_cells = []
        self.game_state = None

        # Lock out other actions while the animation is running
        self._set_controls_state(tk.DISABLED)
        self.stats_label.config(text=f"Running {algorithm_name}...")

        self._search_generator = algorithm_steps(self.model.grid, self.start, goal)
        self._animate_search_step(algorithm_name)


    def _animate_search_step(self, algorithm_name):
        finished_result = None

        for _ in range(self.animation_steps_per_tick):
            try:
                current = next(self._search_generator)
            except StopIteration as finished:
                finished_result = finished.value
                break

            if current != self.start and current not in self._get_treasure_positions():
                self.visited_cells.append(current)

        self.draw_grid()

        if finished_result is not None:
            path, nodes_expanded, runtime = finished_result
            self._finish_search(algorithm_name, path, nodes_expanded, runtime)
            return

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
        goal = self._get_treasure_positions()

        self.path = None
        self.visited_cells = []
        self.game_state = None
        self._heuristic_log = {}

        self._set_controls_state(tk.DISABLED)
        self.stats_label.config(text="Running Greedy Best-First Search...")

        self._search_generator = greedy_best_first_steps(
            self.model.grid, self.start, goal,
            heuristic=manhattan_distance,
            heuristic_log=self._heuristic_log
        )
        self._animate_greedy_step()

    def _animate_greedy_step(self):
        finished_result = None

        for _ in range(self.animation_steps_per_tick):
            try:
                current = next(self._search_generator)
            except StopIteration as finished:
                finished_result = finished.value
                break

            if current != self.start and current not in self._get_treasure_positions():
                self.visited_cells.append(current)

        self.draw_grid()

        if finished_result is not None:
            path, nodes_expanded, runtime = finished_result
            self._finish_greedy_search(path, nodes_expanded, runtime)
            return

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

        reached_treasure = path[-1] if path else None
        start_heuristic = self._heuristic_log.get(self.start)

        print("Path:", path)
        print("Path cost:", path_cost)
        print("Nodes expanded:", nodes_expanded)
        print("Runtime:", runtime)
        print("Heuristic values computed:", self._heuristic_log)

        self.stats_label.config(
            text=f"Greedy Best-First Search finished\n"
                f"Goal treasure: {reached_treasure}\n"
                f"Path cost: {path_cost}\n"
                f"Nodes Expanded: {nodes_expanded}\n"
                f"Execution Time: {runtime:.6f} seconds\n"
                f"Traps Triggered: {traps_triggered}\n"
                f"Start heuristic (Manhattan to goal): {start_heuristic}\n"
                f"Heuristic values computed: {len(self._heuristic_log)}"
        )

        self._set_controls_state(tk.NORMAL)
        
    def run_astar_search(self, heuristic, heuristic_name):
        goal = self._get_treasure_positions()

        self.path = None
        self.visited_cells = []
        self.game_state = None
        self._heuristic_log = {}
        self._astar_heuristic_name = heuristic_name

        self._set_controls_state(tk.DISABLED)
        self.stats_label.config(text=f"Running A* Search ({heuristic_name})...")

        self._search_generator = a_star_steps(
            self.model.grid, self.start, goal,
            heuristic=heuristic,
            heuristic_log=self._heuristic_log
        )
        self._animate_astar_step()

    def _animate_astar_step(self):
        finished_result = None

        for _ in range(self.animation_steps_per_tick):
            try:
                current = next(self._search_generator)
            except StopIteration as finished:
                finished_result = finished.value
                break

            if current != self.start and current not in self._get_treasure_positions():
                self.visited_cells.append(current)

        self.draw_grid()

        if finished_result is not None:
            path, nodes_expanded, runtime = finished_result
            self._finish_astar_search(path, nodes_expanded, runtime)
            return

        self.root.after(self.animation_delay_ms, self._animate_astar_step)

    def _finish_astar_search(self, path, nodes_expanded, runtime):
        self.path = path
        self.draw_grid()

        if path:
            path_cost = compute_path_cost(self.model.grid, path)
            traps_triggered = count_traps_triggered(self.model.grid, path)
        else:
            path_cost = "No path found"
            traps_triggered = 0

        reached_treasure = path[-1] if path else None
        start_heuristic = self._heuristic_log.get(self.start)

        print("Path:", path)
        print("Path cost:", path_cost)
        print("Nodes expanded:", nodes_expanded)
        print("Runtime:", runtime)
        print("Heuristic values computed:", self._heuristic_log)

        self.stats_label.config(
            text=f"A* Search ({self._astar_heuristic_name}) finished\n"
                f"Goal treasure: {reached_treasure}\n"
                f"Path cost: {path_cost}\n"
                f"Nodes Expanded: {nodes_expanded}\n"
                f"Execution Time: {runtime:.6f} seconds\n"
                f"Traps Triggered: {traps_triggered}\n"
                f"Start heuristic ({self._astar_heuristic_name} to goal): {start_heuristic}\n"
                f"Heuristic values computed: {len(self._heuristic_log)}"
        )

        self._set_controls_state(tk.NORMAL)
    
    def run_adversarial(self, algorithm, algorithm_name):
        try:
            depth = int(self.depth_entry.get().strip())
            if depth < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Depth", "Depth must be a positive integer.")
            return

        treasures = self._get_treasure_positions()
        traps = self._get_trap_positions()
        self.game_state = GameState.new_game(self.model.grid, treasures, traps)
        self.path = None
        self.visited_cells = []

        self._set_controls_state(tk.DISABLED)
        self.stats_label.config(text=f"Running {algorithm_name} (depth {depth})...")

        self._game_history, self._game_summary = play_game(self.game_state, algorithm, depth)
        self._game_algorithm_name = algorithm_name
        self._game_depth = depth
        self._game_step_index = 0

        self.draw_grid()
        self._animate_game_step()

    def _animate_game_step(self):
        if self._game_step_index >= len(self._game_history):
            self._finish_adversarial_game()
            return

        turn_record = self._game_history[self._game_step_index]
        self.game_state = turn_record["state"]
        self._game_step_index += 1

        self.draw_grid()
        self.root.after(self.animation_delay_ms, self._animate_game_step)

    def _finish_adversarial_game(self):
        summary = self._game_summary
        prune_line = (
            f"Prunes: {summary['prunes']}  Pruning ratio: {summary['pruning_ratio']:.2%}\n"
            if self._game_algorithm_name == "Alpha-Beta" else ""
        )

        self.stats_label.config(
            text=f"{self._game_algorithm_name} (depth {self._game_depth}) finished\n"
                f"Turns played: {summary['turns']}\n"
                f"Nodes Expanded: {summary['nodes_expanded']}\n"
                f"Execution Time: {summary['runtime']:.6f} seconds\n"
                f"{prune_line}"
                f"Treasures -- A: {summary['treasures_collected']['A']}  "
                f"B: {summary['treasures_collected']['B']}\n"
                f"Outcome (Agent A): {summary['outcome']}"
        )

        self._set_controls_state(tk.NORMAL)
        
if __name__ == "__main__":
    root = tk.Tk()
    app = TreasureHuntGUI(root)
    root.mainloop()