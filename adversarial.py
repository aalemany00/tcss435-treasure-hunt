"""
Adversarial search for the Treasure Hunt grid (TCSS 435, Assignment 3).

Two agents (A, B) alternate turns on a static grid of walls/traps/treasures.
Each turn, an agent moves one step (up/down/left/right) or stays in place.
Landing on a treasure collects it (removes it from the board); landing on
a trap applies a penalty. The game ends when no treasures remain or a
maximum number of turns is reached.

    score, move, nodes_expanded, runtime = minimax(state, depth)
    score, move, nodes_expanded, runtime, prunes = alpha_beta(state, depth)
"""

import time
from TreasureGridModel import STATIC_WALL, TRAP, TREASURE

MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]  # up, down, left, right, stay

TRAP_PENALTY = 10  # penalty for landing on a trap
TREASURE_BONUS = 100


class GameState:
    """
    Minimal, copy-on-move game state: the grid's static layout (walls) plus
    whatever changes turn to turn (remaining treasures, trap positions,
    both agents' coordinates, and whose turn it is).
    """

    def __init__(self, grid, agent_a_pos, agent_b_pos, treasures, traps, turn="A", a_collected=0, b_collected=0):
        self.grid = grid
        self.agent_a_pos = agent_a_pos
        self.agent_b_pos = agent_b_pos
        self.treasures = set(treasures)
        self.traps = set(traps)
        self.turn = turn
        self.a_collected = a_collected
        self.b_collected = b_collected

    @classmethod
    def new_game(cls, grid, treasures, traps, agent_a_pos=None, agent_b_pos=None, turn="A"):
        """
        Build a starting GameState. Agent A defaults to the top-left corner
        and Agent B to the bottom-right corner -- opposite corners keep the
        game fair, since neither agent starts closer to the scattered
        treasures than the other on average.
        """
        n_rows, n_cols = grid.shape
        if agent_a_pos is None:
            agent_a_pos = (0, 0)
        if agent_b_pos is None:
            agent_b_pos = (n_rows - 1, n_cols - 1)
        return cls(grid, agent_a_pos, agent_b_pos, treasures, traps, turn)

    def is_walkable(self, row, col):
        n_rows, n_cols = self.grid.shape
        if not (0 <= row < n_rows and 0 <= col < n_cols):
            return False
        return self.grid[row, col] != STATIC_WALL

    def legal_moves(self):
        row, col = self.agent_a_pos if self.turn == "A" else self.agent_b_pos
        moves = []
        for d_row, d_col in MOVES:
            new_row, new_col = row + d_row, col + d_col
            if self.is_walkable(new_row, new_col):
                moves.append((new_row, new_col))
        return moves

    def apply_move(self, new_pos):
        """Returns a NEW GameState after the current player moves to new_pos."""
        treasures = set(self.treasures)
        collected_this_move = new_pos in treasures
        treasures.discard(new_pos)  # collect a treasure if standing on one

        a_collected = self.a_collected + (1 if self.turn == "A" and collected_this_move else 0)
        b_collected = self.b_collected + (1 if self.turn == "B" and collected_this_move else 0)

        next_state = GameState(
            self.grid,
            new_pos if self.turn == "A" else self.agent_a_pos,
            new_pos if self.turn == "B" else self.agent_b_pos,
            treasures,
            self.traps,
            turn="B" if self.turn == "A" else "A",
            a_collected=a_collected,
            b_collected=b_collected,
        )
        return next_state

    def is_terminal(self):
        return len(self.treasures) == 0


def manhattan(pos_a, pos_b):
    return abs(pos_a[0] - pos_b[0]) + abs(pos_a[1] - pos_b[1])


def evaluate(state):
    """
    Heuristic evaluation from Agent A's perspective: positive favors A,
    negative favors B. Combines:
      - distance to the nearest remaining treasure (closer is better)
      - proximity to traps (closer is worse)
      - a strong bonus per treasure each agent has actually collected,
        so collecting is always better than camping near an uncollected one
      - the same factors for B, subtracted (relative advantage)
    """
    def agent_score(agent_pos, other_pos):
        if not state.treasures:
            return 0  # no treasures left

        nearest_treasure_dist = min(manhattan(agent_pos, t) for t in state.treasures)
        score = -nearest_treasure_dist

        if state.traps:
            nearest_trap_dist = min(manhattan(agent_pos, x) for x in state.traps)
            if nearest_trap_dist == 0:
                score -= TRAP_PENALTY  # landed on a trap
            else:
                score -= 1.0 / nearest_trap_dist  # closer traps hurt more

        return score

    a_score = agent_score(state.agent_a_pos, state.agent_b_pos) + TREASURE_BONUS * state.a_collected
    b_score = agent_score(state.agent_b_pos, state.agent_a_pos) + TREASURE_BONUS * state.b_collected

    return a_score - b_score  # positive favors A, negative favors B


def minimax(state, depth):
    """
    Plain Minimax with depth-limited evaluation. Agent A maximizes,
    Agent B minimizes. Returns (score, best_move, nodes_expanded, runtime).
    """
    start_time = time.perf_counter()
    nodes_expanded = 0

    def recurse(state, depth):
        nonlocal nodes_expanded
        nodes_expanded += 1

        if depth == 0 or state.is_terminal():
            return evaluate(state), None

        maximizing = state.turn == "A"
        best_move = None
        best_score = None
        best_key = None

        for move in state.legal_moves():
            child = state.apply_move(move)
            score, _ = recurse(child, depth - 1)

            # When two moves tie on deep value, prefer whichever looks better
            # right now (1-ply). Without this, "collect the last treasure now"
            # and "wander for a few turns, then collect it" can score identically
            # at depth -- minimax has no inherent notion that sooner is better --
            # so it can pick either one arbitrarily, which looks like the agent
            # aimlessly orbiting a treasure instead of taking it.
            immediate = evaluate(child)
            key = (score, immediate) if maximizing else (-score, -immediate)

            if best_key is None or key > best_key:
                best_key, best_score, best_move = key, score, move

        return best_score, best_move

    score, move = recurse(state, depth)
    return score, move, nodes_expanded, time.perf_counter() - start_time


def alpha_beta(state, depth):
    """
    Minimax with alpha-beta pruning. Same interface as minimax(), plus a
    pruning count so the assignment's "observed pruning ratio" can be
    reported: pruning_ratio = prunes / (nodes_expanded + prunes).
    Returns (score, best_move, nodes_expanded, runtime, prunes).
    """
    start_time = time.perf_counter()
    nodes_expanded = 0
    prunes = 0

    def recurse(state, depth, alpha, beta):
        nonlocal nodes_expanded, prunes
        nodes_expanded += 1

        if depth == 0 or state.is_terminal():
            return evaluate(state), None

        maximizing = state.turn == "A"
        best_move = None
        best_score = None
        best_key = None

        for move in state.legal_moves():
            child = state.apply_move(move)
            score, _ = recurse(child, depth - 1, alpha, beta)

            # See minimax() for why this tiebreak exists.
            immediate = evaluate(child)
            key = (score, immediate) if maximizing else (-score, -immediate)

            if best_key is None or key > best_key:
                best_key, best_score, best_move = key, score, move

            if maximizing:
                alpha = max(alpha, best_score)
            else:
                beta = min(beta, best_score)

            if beta <= alpha:
                prunes += 1
                break  # prune remaining siblings

        return best_score, best_move

    score, move = recurse(state, depth, float("-inf"), float("inf"))
    return score, move, nodes_expanded, time.perf_counter() - start_time, prunes

def play_game(state, algorithm, depth, max_turns=200):
    """
    Play a full game by having BOTH agents use `algorithm` (minimax or
    alpha_beta) to choose their move each turn, until no treasures remain
    or max_turns is reached. Returns (history, summary): history is a list
    of {"turn": "A"/"B", "move": pos, "state": GameState after the move},
    so the GUI can animate the game move by move; summary has the totals
    the assignment's Summary Table asks for.
    """
    history = []
    total_nodes = 0
    total_prunes = 0
    total_runtime = 0.0
    treasures_collected = {"A": 0, "B": 0}

    turn_count = 0
    while not state.is_terminal() and turn_count < max_turns:
        mover = state.turn
        result = algorithm(state, depth)

        if algorithm is alpha_beta:
            score, move, nodes, runtime, prunes = result
            total_prunes += prunes
        else:
            score, move, nodes, runtime = result

        total_nodes += nodes
        total_runtime += runtime

        if move is None:
            break  # no legal moves available

        if move in state.treasures:
            treasures_collected[mover] += 1

        state = state.apply_move(move)
        history.append({"turn": mover, "move": move, "state": state})
        turn_count += 1

    if treasures_collected["A"] > treasures_collected["B"]:
        outcome = "Win"
    elif treasures_collected["A"] < treasures_collected["B"]:
        outcome = "Loss"
    else:
        outcome = "Draw"

    summary = {
        "nodes_expanded": total_nodes,
        "runtime": total_runtime,
        "prunes": total_prunes,
        "pruning_ratio": total_prunes / (total_nodes + total_prunes) if (total_nodes + total_prunes) else 0.0,
        "treasures_collected": treasures_collected,
        "outcome": outcome,
        "turns": turn_count,
    }
    return history, summary