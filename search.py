"""
Uninformed search algorithms for the Treasure Hunt grid (TCSS 435, Assignment 1).
 
Every search function has the same signature and return format so the GUI and
experiment code can treat them interchangeably:
 
    path, nodes_expanded, runtime = bfs(grid, start, goal)
 
Movement: 4-directional (up, down, left, right), each step costs 1.
Static walls and the trap are treated as blocked cells, so the agent never
steps on a trap. The treasure cell is the goal and is always enterable.
"""

import time
import heapq
from collections import deque

from TreasureGridModel import STATIC_WALL, TRAP

# Neighbor order matters for DFS/BFS tie-breaking: 
MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right 


# Shared Helpers

def is_walkable(grid, row, col):
    """True if (row, col) is inside the grid and is not a wall or trap."""
    n_rows, n_cols = grid.shape
    if not(0 <= row < n_rows and 0 <= col < n_cols):
        return False
    return grid[row, col] != STATIC_WALL and grid[row, col] != TRAP


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


def _start_is_valid(grid, start):
    return is_walkable(grid, start[0], start[1])


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
    
    if _start_is_valid(grid, start):
        frontier = deque([start])
        parent = {start: None} # doubles as the visited set
        
        while frontier:
            current = frontier.popleft()
            nodes_expanded += 1
            
            if current == goal:
                path = reconstruct_path(parent, goal)
                break
            
            for neighbor in get_neighbors(grid, current):
                if neighbor not in parent:
                    parent[neighbor] = current
                    frontier.append(neighbor)
                    
    return path, nodes_expanded, time.perf_counter() - start_time


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
    
    if _start_is_valid(grid, start):
        frontier = [(start, None)] # (node, parent)
        parent = {} # filled in when a node is expanded
        
        while frontier:
            current, came_from = frontier.pop()
            if current in parent:   # already expanded via another route
                continue
 
            parent[current] = came_from
            nodes_expanded += 1
 
            if current == goal:
                path = reconstruct_path(parent, goal)
                break
 
            # Reversed so the first move in MOVES is explored first.
            for neighbor in reversed(get_neighbors(grid, current)):
                if neighbor not in parent:
                    frontier.append((neighbor, current))
 
    return path, nodes_expanded, time.perf_counter() - start_time

# Uniform Cost Search (UCS)

def ucs(grid, start, goal):
    """
    Find the lowest-cost path to the treasure using UCS.
    Uses a priority queue to explore the cheapest paths first.
    """
    start_time = time.perf_counter()
    nodes_expanded = 0
    path = None

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

            # Stop once the treasure is found
            if current == goal:
                path = reconstruct_path(parent, goal)
                break

            # Check all valid neighboring cells
            for neighbor in get_neighbors(grid, current):
                new_cost = current_cost + 1

                if neighbor not in costs or new_cost < costs[neighbor]:
                    costs[neighbor] = new_cost
                    parent[neighbor] = current
                    heapq.heappush(frontier, (new_cost, neighbor))

    return path, nodes_expanded, time.perf_counter() - start_time