"""
Heuristic functions for informed search (TCSS 435, Assignment 2).

Both heuristics estimate the cost remaining from a position to a goal
position on the grid. A* and Greedy Best-First Search both use them to
decide which frontier position to expand next.
"""


def manhattan_distance(pos, goal):
    """|dx| + |dy| -- admissible for 4-directional movement with unit step cost."""
    row, col = pos
    goal_row, goal_col = goal
    return abs(row - goal_row) + abs(col - goal_col)


def euclidean_distance(pos, goal):
    """
    Straight-line distance -- also admissible, but a looser (smaller)
    estimate than Manhattan distance when movement is 4-directional, since
    it ignores that diagonal movement isn't allowed.
    """
    row, col = pos
    goal_row, goal_col = goal
    return ((row - goal_row) ** 2 + (col - goal_col) ** 2) ** 0.5


def closest_treasure(pos, treasures, heuristic=manhattan_distance):
    """
    Pick whichever treasure the heuristic ranks as cheapest to reach from
    pos. With multiple treasures on the grid, informed search needs one
    definite goal to aim for -- this gives Greedy and A* the same target
    so their results are comparable.
    """
    return min(treasures, key=lambda t: heuristic(pos, t))