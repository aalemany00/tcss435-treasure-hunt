"""
Uninformed search algorithms for the Treasure Hunt grid (TCSS 435, Assignment 1).

Every search function has the same signature and return format so the GUI and
experiment code can treat them interchangeably:

    path, nodes_expanded, runtime = bfs(grid, start, goal)

Movement: 4-directional (up, down, left, right). Static walls are
impassable; traps are walkable but cost more than a normal move (see
move_cost()). The treasure cell is the goal and is always enterable.
"""

import time
import heapq
from collections import deque
from heuristics import manhattan_distance
from TreasureGridModel import STATIC_WALL, TRAP

# Neighbor order matters for DFS/BFS tie-breaking: 
MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right 

# Movement cost constants
NORMAL_MOVE_COST = 1
TRAP_COST = 5  # passable, but costs more than a normal move


def move_cost(grid, row, col):
    """Cost of stepping onto (row, col). Traps are walkable but expensive;
    everything else costs the standard 1 per move."""
    if grid[row, col] == TRAP:
        return TRAP_COST
    return NORMAL_MOVE_COST

# Shared Helpers

def is_walkable(grid, row, col):
    """True if (row, col) is inside the grid and is not a static wall.
    Traps are walkable -- at a higher cost via move_cost() -- only static
    walls are truly impassable."""
    n_rows, n_cols = grid.shape
    if not (0 <= row < n_rows and 0 <= col < n_cols):
        return False
    return grid[row, col] != STATIC_WALL


def get_neighbors(grid, pos):
    """Return a list of walkable neighbor positions for the given position."""
    row, col = pos
    neighbors = []
    for d_row, d_col in MOVES:
        new_row, new_col = row + d_row, col + d_col
        if is_walkable(grid, new_row, new_col):
            neighbors.append((new_row, new_col))
    return neighbors


def reconstruct_path(parent, goal):
    """Walk the parent map backwards from the goal to start, then reverse it."""
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent.get(node)
    path.reverse()
    return path


def compute_path_cost(grid, path):
    """
    Sum of actual movement costs along a path, accounting for the higher
    trap cost. Use this instead of len(path) - 1 now that not all moves
    cost the same.
    """
    if not path or len(path) < 2:
        return 0
    return sum(move_cost(grid, row, col) for row, col in path[1:])


def count_traps_triggered(grid, path):
    """Number of trap cells stepped on along a path (for leaderboard scoring)."""
    if not path:
        return 0
    return sum(1 for row, col in path if grid[row, col] == TRAP)


def _start_is_valid(grid, start):
    return is_walkable(grid, start[0], start[1])

def _as_goal_set(goal):
    """
    Normalize `goal` to a set of (row, col) positions. Accepts either a
    single (row, col) tuple or an iterable of them, so a search can stop
    at ANY one of several treasures instead of only a single pre-chosen one.
    """
    if isinstance(goal, tuple) and len(goal) == 2 and isinstance(goal[0], int):
        return {goal}
    return set(goal)

# Breadth-First Search (BFS)

def bfs(grid, start, goal):
    """
    Breadth-First search using FIFO queue.
    
    Explores level by level, so with unit step costs the path it finds is
    always the shortest one.
    """
    start_time = time.perf_counter()
    nodes_expanded = 0
    path = None
    
    goals = _as_goal_set(goal)

    if _start_is_valid(grid, start):
        frontier = deque([start])
        parent = {start: None} # doubles as the visited set

        while frontier:
            current = frontier.popleft()
            nodes_expanded += 1

            if current in goals:
                path = reconstruct_path(parent, current)
                break

            for neighbor in get_neighbors(grid, current):
                if neighbor not in parent:
                    parent[neighbor] = current
                    frontier.append(neighbor)

    return path, nodes_expanded, time.perf_counter() - start_time


def bfs_steps(grid, start, goal):
    """
    Generator version of bfs() for step-by-step GUI animation.

    Yields each position as it is expanded (visited), one at a time, so the
    caller can redraw between steps. Runtime only counts the algorithm's
    own computation -- not the time spent paused between animation frames
    while the GUI is waiting to call next() again.
    """
    elapsed = 0.0
    nodes_expanded = 0
    path = None

    goals = _as_goal_set(goal)

    if _start_is_valid(grid, start):
        frontier = deque([start])
        parent = {start: None}

        while frontier:
            step_start = time.perf_counter()
            current = frontier.popleft()
            nodes_expanded += 1

            if current in goals:
                path = reconstruct_path(parent, current)
                elapsed += time.perf_counter() - step_start
                yield current
                break

            for neighbor in get_neighbors(grid, current):
                if neighbor not in parent:
                    parent[neighbor] = current
                    frontier.append(neighbor)

            elapsed += time.perf_counter() - step_start
            yield current

    return path, nodes_expanded, elapsed


# Depth-First Search (DFS)

def dfs(grid, start, goal):
    """
    Depth-First search using LIFO stack.
    
    Explores as far as possible along each branch before backtracking.
    The path it finds may not be the shortest one.
    """
    start_time = time.perf_counter()
    nodes_expanded = 0
    path = None
    
    goals = _as_goal_set(goal)

    if _start_is_valid(grid, start):
        frontier = [(start, None)] # (node, parent)
        parent = {} # filled in when a node is expanded

        while frontier:
            current, came_from = frontier.pop()
            if current in parent:   # already expanded via another route
                continue

            parent[current] = came_from
            nodes_expanded += 1

            if current in goals:
                path = reconstruct_path(parent, current)
                break
 
            # Reversed so the first move in MOVES is explored first.
            for neighbor in reversed(get_neighbors(grid, current)):
                if neighbor not in parent:
                    frontier.append((neighbor, current))

    return path, nodes_expanded, time.perf_counter() - start_time


def dfs_steps(grid, start, goal):
    """Generator version of dfs() for step-by-step GUI animation. See bfs_steps()."""
    elapsed = 0.0
    nodes_expanded = 0
    path = None

    goals = _as_goal_set(goal)

    if _start_is_valid(grid, start):
        frontier = [(start, None)]
        parent = {}

        while frontier:
            step_start = time.perf_counter()
            current, came_from = frontier.pop()

            if current in parent:
                elapsed += time.perf_counter() - step_start
                continue

            parent[current] = came_from
            nodes_expanded += 1

            if current in goals:
                path = reconstruct_path(parent, current)
                elapsed += time.perf_counter() - step_start
                yield current
                break

            for neighbor in reversed(get_neighbors(grid, current)):
                if neighbor not in parent:
                    frontier.append((neighbor, current))

            elapsed += time.perf_counter() - step_start
            yield current

    return path, nodes_expanded, elapsed

# Uniform Cost Search (UCS)

def ucs(grid, start, goal):
    """
    Find the lowest-cost path to the treasure using UCS.
    Uses a priority queue to explore the cheapest paths first.
    """
    start_time = time.perf_counter()
    nodes_expanded = 0
    path = None

    goals = _as_goal_set(goal)

    if _start_is_valid(grid, start):
        # Priority queue stores (total_cost, position)
        frontier = [(0, start)]

        # Keep track of the lowest cost to each position
        costs = {start: 0}
        parent = {start: None}
        visited = set()

        while frontier:
            current_cost, current = heapq.heappop(frontier)

            # Skip positions that have already been expanded
            if current in visited:
                continue

            visited.add(current)
            nodes_expanded += 1

            # Stop once any treasure is found
            if current in goals:
                path = reconstruct_path(parent, current)
                break

            # Check all valid neighboring cells
            for neighbor in get_neighbors(grid, current):
                new_cost = current_cost + move_cost(grid, *neighbor)

                if neighbor not in costs or new_cost < costs[neighbor]:
                    costs[neighbor] = new_cost
                    parent[neighbor] = current
                    heapq.heappush(frontier, (new_cost, neighbor))

    return path, nodes_expanded, time.perf_counter() - start_time


def ucs_steps(grid, start, goal):
    """Generator version of ucs() for step-by-step GUI animation. See bfs_steps()."""
    elapsed = 0.0
    nodes_expanded = 0
    path = None

    goals = _as_goal_set(goal)

    if _start_is_valid(grid, start):
        frontier = [(0, start)]
        costs = {start: 0}
        parent = {start: None}
        visited = set()

        while frontier:
            step_start = time.perf_counter()
            current_cost, current = heapq.heappop(frontier)

            if current in visited:
                elapsed += time.perf_counter() - step_start
                continue

            visited.add(current)
            nodes_expanded += 1

            if current in goals:
                path = reconstruct_path(parent, current)
                elapsed += time.perf_counter() - step_start
                yield current
                break

            for neighbor in get_neighbors(grid, current):
                new_cost = current_cost + move_cost(grid, *neighbor)
                if neighbor not in costs or new_cost < costs[neighbor]:
                    costs[neighbor] = new_cost
                    parent[neighbor] = current
                    heapq.heappush(frontier, (new_cost, neighbor))

            elapsed += time.perf_counter() - step_start
            yield current

    return path, nodes_expanded, elapsed

# Greedy Best-First Search

def greedy_best_first(grid, start, goal, heuristic=manhattan_distance, heuristic_log=None):
    """
    Greedy Best-First Search: always expands the frontier position that the
    heuristic estimates as closest to the goal, ignoring the path cost
    already spent to reach it. Usually faster than A*, but -- unlike A* --
    not guaranteed to find the cheapest path.

    If `heuristic_log` is given (a dict), it's filled in with the heuristic
    value computed for every position considered, so results can report
    "heuristic values computed" as the assignment requires.
    """
    start_time = time.perf_counter()
    nodes_expanded = 0
    path = None

    goals = _as_goal_set(goal)

    if _start_is_valid(grid, start):
        start_h = min(heuristic(start, g) for g in goals)
        if heuristic_log is not None:
            heuristic_log[start] = start_h

        frontier = [(start_h, start)]
        parent = {start: None}
        visited = set()

        while frontier:
            _, current = heapq.heappop(frontier)

            if current in visited:
                continue
            visited.add(current)
            nodes_expanded += 1

            if current in goals:
                path = reconstruct_path(parent, current)
                break

            for neighbor in get_neighbors(grid, current):
                if neighbor not in parent:
                    parent[neighbor] = current
                    h = min(heuristic(neighbor, g) for g in goals)
                    if heuristic_log is not None:
                        heuristic_log[neighbor] = h
                    heapq.heappush(frontier, (h, neighbor))

    return path, nodes_expanded, time.perf_counter() - start_time


def greedy_best_first_steps(grid, start, goal, heuristic=manhattan_distance, heuristic_log=None):
    """Generator version of greedy_best_first() for step-by-step GUI animation. See bfs_steps()."""
    elapsed = 0.0
    nodes_expanded = 0
    path = None

    goals = _as_goal_set(goal)

    if _start_is_valid(grid, start):
        step_start = time.perf_counter()
        start_h = min(heuristic(start, g) for g in goals)
        if heuristic_log is not None:
            heuristic_log[start] = start_h
        frontier = [(start_h, start)]
        parent = {start: None}
        visited = set()
        elapsed += time.perf_counter() - step_start

        while frontier:
            step_start = time.perf_counter()
            _, current = heapq.heappop(frontier)

            if current in visited:
                elapsed += time.perf_counter() - step_start
                continue

            visited.add(current)
            nodes_expanded += 1

            if current in goals:
                path = reconstruct_path(parent, current)
                elapsed += time.perf_counter() - step_start
                yield current
                break

            for neighbor in get_neighbors(grid, current):
                if neighbor not in parent:
                    parent[neighbor] = current
                    h = min(heuristic(neighbor, g) for g in goals)
                    if heuristic_log is not None:
                        heuristic_log[neighbor] = h
                    heapq.heappush(frontier, (h, neighbor))

            elapsed += time.perf_counter() - step_start
            yield current

    return path, nodes_expanded, elapsed

def a_star(grid, start, goal, heuristic=manhattan_distance, heuristic_log=None):
    """
    A* search: expands the frontier position with the lowest f(n) = g(n) + h(n),
    where g(n) is the real cost from start and h(n) is the heuristic estimate
    to the goal. Finds the lowest-cost path when the heuristic is admissible,
    while typically expanding far fewer nodes than UCS.
    """
    start_time = time.perf_counter()
    nodes_expanded = 0
    path = None

    goals = _as_goal_set(goal)

    if _start_is_valid(grid, start):
        h = min(heuristic(start, g) for g in goals)
        frontier = [(h, 0, start)]
        costs = {start: 0}
        parent = {start: None}
        visited = set()

        if heuristic_log is not None:
            heuristic_log[start] = h

        while frontier:
            f_cost, current_cost, current = heapq.heappop(frontier)

            if current in visited:
                continue

            visited.add(current)
            nodes_expanded += 1

            if current in goals:
                path = reconstruct_path(parent, current)
                break

            for neighbor in get_neighbors(grid, current):
                new_cost = current_cost + move_cost(grid, *neighbor)
                if neighbor not in costs or new_cost < costs[neighbor]:
                    costs[neighbor] = new_cost
                    parent[neighbor] = current

                    h = min(heuristic(neighbor, g) for g in goals)
                    f_cost = new_cost + h

                    heapq.heappush(frontier, (f_cost, new_cost, neighbor))

                    if heuristic_log is not None:
                        heuristic_log[neighbor] = h

    return path, nodes_expanded, time.perf_counter() - start_time

def a_star_steps(grid, start, goal, heuristic=manhattan_distance, heuristic_log=None):
    """
    Generator version of a_star() for step-by-step GUI animation. Runtime
    only counts the algorithm's own computation -- not the time spent paused
    between animation frames while the GUI is waiting to call next() again.
    """
    elapsed = 0.0
    nodes_expanded = 0
    path = None

    goals = _as_goal_set(goal)
    goal_not_found = True
    start_valid = _start_is_valid(grid, start)

    step_start = time.perf_counter()
    h = min(heuristic(start, g) for g in goals)
    frontier = [(h, 0, start)]
    costs = {start: 0}
    parent = {start: None}
    visited = set()

    if heuristic_log is not None:
        heuristic_log[start] = h
    elapsed += time.perf_counter() - step_start

    while start_valid and goal_not_found and frontier:
        step_start = time.perf_counter()
        f_cost, current_cost, current = heapq.heappop(frontier)

        if current not in visited:
            elapsed += time.perf_counter() - step_start
            # Yield the current position so the GUI can animate it.
            yield current
            step_start = time.perf_counter()

            for neighbor in get_neighbors(grid, current):
                new_cost = current_cost + move_cost(grid, *neighbor)

                if neighbor not in costs or new_cost < costs[neighbor]:
                    costs[neighbor] = new_cost
                    parent[neighbor] = current

                    h = min(heuristic(neighbor, g) for g in goals)
                    f_cost = new_cost + h

                    heapq.heappush(frontier, (f_cost, new_cost, neighbor))

                    if heuristic_log is not None:
                        heuristic_log[neighbor] = h

            visited.add(current)
            nodes_expanded += 1

        if current in goals:
            path = reconstruct_path(parent, current)
            goal_not_found = False

        elapsed += time.perf_counter() - step_start

    return path, nodes_expanded, elapsed