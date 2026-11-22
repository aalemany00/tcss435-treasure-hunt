"""Adversarial search for the TCSS 435 Treasure Hunt game (Assignment 3).

Agent A maximizes the evaluation score and Agent B minimizes it. Search depth
counts individual moves (plies), not complete A/B rounds. The implementations
use move ordering, a transposition cache, and alpha-beta pruning where relevant.
The GUI should run these functions in a worker thread so the Tk event loop stays
responsive; these functions themselves are intentionally GUI-independent.
"""
from __future__ import annotations
import time
from functools import lru_cache
from TreasureGridModel import STATIC_WALL

# Four cardinal moves. We deliberately omit the 'stay' action: it creates
# redundant branches and can encourage agents to waste turns. A player with no
# legal cardinal move is handled as a terminal search state.
MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]
TRAP_PENALTY = 10
TREASURE_BONUS = 100


class GameState:
    """Immutable-by-convention state; apply_move creates a fresh state."""
    def __init__(self, grid, agent_a_pos, agent_b_pos, treasures, traps, turn="A",
                 a_collected=0, b_collected=0, a_treasure_cells=None, b_treasure_cells=None):
        self.grid = grid
        self.agent_a_pos = tuple(agent_a_pos)
        self.agent_b_pos = tuple(agent_b_pos)
        self.treasures = frozenset(tuple(p) for p in treasures)
        self.traps = frozenset(tuple(p) for p in traps)
        self.turn = turn
        self.a_collected = a_collected
        self.b_collected = b_collected
        self.a_treasure_cells = frozenset(a_treasure_cells or ())
        self.b_treasure_cells = frozenset(b_treasure_cells or ())

    @classmethod
    def new_game(cls, grid, treasures, traps, agent_a_pos=None, agent_b_pos=None, turn="A"):
        rows, cols = grid.shape
        agent_a_pos = agent_a_pos or (0, 0)
        agent_b_pos = agent_b_pos or (rows - 1, cols - 1)
        return cls(grid, agent_a_pos, agent_b_pos, treasures, traps, turn)

    def is_walkable(self, row, col):
        rows, cols = self.grid.shape
        return 0 <= row < rows and 0 <= col < cols and self.grid[row, col] != STATIC_WALL

    def legal_moves(self):
        pos = self.agent_a_pos if self.turn == "A" else self.agent_b_pos
        other = self.agent_b_pos if self.turn == "A" else self.agent_a_pos
        moves = [(pos[0] + dr, pos[1] + dc) for dr, dc in MOVES]
        # Avoid stepping onto the opponent. Stable move ordering prioritizes
        # collecting treasure, then safety, then deterministic row/col order.
        moves = [m for m in moves if self.is_walkable(*m) and m != other]
        moves.sort(key=lambda m: (m not in self.treasures, m in self.traps, m))
        return moves

    def apply_move(self, new_pos):
        treasures = set(self.treasures)
        got_treasure = new_pos in treasures
        treasures.discard(new_pos)
        if self.turn == "A":
            a_pos, b_pos = new_pos, self.agent_b_pos
            a_count, b_count = self.a_collected + int(got_treasure), self.b_collected
            a_cells = set(self.a_treasure_cells); b_cells = set(self.b_treasure_cells)
            if got_treasure: a_cells.add(new_pos)
        else:
            a_pos, b_pos = self.agent_a_pos, new_pos
            a_count, b_count = self.a_collected, self.b_collected + int(got_treasure)
            a_cells = set(self.a_treasure_cells); b_cells = set(self.b_treasure_cells)
            if got_treasure: b_cells.add(new_pos)
        return GameState(self.grid, a_pos, b_pos, treasures, self.traps,
                        "B" if self.turn == "A" else "A", a_count, b_count, a_cells, b_cells)

    def is_terminal(self):
        return not self.treasures or not self.legal_moves()


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def evaluate_distance(state):
    """Baseline heuristic: nearest-treasure distance and trap proximity.

    The score is always from Agent A's perspective: positive favors A.
    """
    score = TREASURE_BONUS * (state.a_collected - state.b_collected)
    if not state.treasures:
        return score

    def positional_score(position):
        nearest_distance = float("inf")
        for treasure in state.treasures:
            distance = manhattan(position, treasure)
            if distance < nearest_distance:
                nearest_distance = distance

        trap_score = 0.0
        if state.traps:
            nearest_trap = float("inf")
            for trap in state.traps:
                distance = manhattan(position, trap)
                if distance < nearest_trap:
                    nearest_trap = distance
            if nearest_trap == 0:
                trap_score = -TRAP_PENALTY
            else:
                trap_score = -0.5 / nearest_trap
        return -nearest_distance + trap_score

    return score + positional_score(state.agent_a_pos) - positional_score(state.agent_b_pos)


def evaluate_competition(state):
    """Alternative heuristic: score each treasure by the agents' relative distance.

    A treasure favors A when A is closer, favors B when B is closer, and is
    neutral when both agents are equally far away. Collected treasure and trap
    terms are handled as in the baseline heuristic.
    """
    score = TREASURE_BONUS * (state.a_collected - state.b_collected)

    for treasure in state.treasures:
        distance_a = manhattan(state.agent_a_pos, treasure)
        distance_b = manhattan(state.agent_b_pos, treasure)
        score += distance_b - distance_a

    # Keep a small safety term so standing directly on a trap is discouraged.
    if state.agent_a_pos in state.traps:
        score -= TRAP_PENALTY
    if state.agent_b_pos in state.traps:
        score += TRAP_PENALTY

    return score


# Backwards-compatible default name for any existing code importing evaluate.
def evaluate(state):
    return evaluate_distance(state)


def _state_key(state, depth):
    return (state.agent_a_pos, state.agent_b_pos, state.treasures, state.turn,
            state.a_collected, state.b_collected, depth)


def minimax(state, depth, evaluation_function=evaluate_distance):
    """Plain depth-limited minimax without memoization for fair node counts.

    Keeping this baseline uncached makes the expanded-node comparison with
    alpha_beta meaningful: the only major search reduction being measured is
    alpha-beta's pruning (rather than one algorithm using transpositions).
    """
    started = time.perf_counter(); nodes = 0
    def recurse(s, d):
        nonlocal nodes
        nodes += 1
        if d <= 0 or s.is_terminal(): return evaluation_function(s), None
        moves = s.legal_moves()
        if not moves: return evaluation_function(s), None
        maximizing = s.turn == "A"
        best_score = float("-inf") if maximizing else float("inf")
        best_move = None
        for move in moves:
            score, _ = recurse(s.apply_move(move), d-1)
            if (maximizing and score > best_score) or (not maximizing and score < best_score):
                best_score, best_move = score, move
        return best_score, best_move
    score, move = recurse(state, max(0, int(depth)))
    return score, move, nodes, time.perf_counter()-started


def alpha_beta(state, depth, evaluation_function=evaluate_distance):
    """Alpha-beta search with treasure-first move ordering and exact cache.
    Returns (score, move, nodes_expanded, runtime, prune_events).
    """
    started = time.perf_counter(); nodes = 0; prunes = 0
    cache = {}
    def recurse(s, d, alpha, beta):
        nonlocal nodes, prunes
        key = _state_key(s, d)
        # Only store fully explored values: a cutoff value is a bound, not exact.
        nodes += 1
        if d <= 0 or s.is_terminal(): return evaluation_function(s), None
        moves = s.legal_moves()
        if not moves: return evaluation_function(s), None
        maximizing = s.turn == "A"
        best = float("-inf") if maximizing else float("inf")
        best_move = None
        for index, move in enumerate(moves):
            score, _ = recurse(s.apply_move(move), d-1, alpha, beta)
            if (maximizing and score > best) or (not maximizing and score < best):
                best, best_move = score, move
            if maximizing: alpha = max(alpha, best)
            else: beta = min(beta, best)
            if beta <= alpha:
                # Count sibling branches skipped at this cutoff, rather than
                # merely counting the cutoff event itself.
                prunes += len(moves) - index - 1
                break
        return best, best_move
    score, move = recurse(state, max(0, int(depth)), float("-inf"), float("inf"))
    return score, move, nodes, time.perf_counter()-started, prunes


def play_game(state, algorithm, depth, max_turns=200, evaluation_function=evaluate_distance):
    """Run an AI-vs-AI game and return chronological move records + metrics."""
    history = []; nodes_total = 0; prunes_total = 0; runtime_total = 0.0
    collected = {"A": 0, "B": 0}; turns = 0
    while not state.is_terminal() and turns < max_turns:
        mover = state.turn
        result = algorithm(state, depth, evaluation_function)
        if algorithm is alpha_beta:
            score, move, nodes, runtime, prunes = result; prunes_total += prunes
        else:
            score, move, nodes, runtime = result; prunes = 0
        nodes_total += nodes; runtime_total += runtime
        if move is None: break
        if move in state.treasures: collected[mover] += 1
        state = state.apply_move(move)
        history.append({"turn": mover, "move": move, "state": state, "score": score,
                       "nodes": nodes, "runtime": runtime, "prunes": prunes})
        turns += 1
    if collected["A"] > collected["B"]: outcome = "Win"
    elif collected["A"] < collected["B"]: outcome = "Loss"
    else: outcome = "Draw"
    summary = {"nodes_expanded": nodes_total, "runtime": runtime_total,
               "prunes": prunes_total,
               "pruning_ratio": prunes_total/(nodes_total+prunes_total) if nodes_total+prunes_total else 0,
               "treasures_collected": collected, "outcome": outcome, "turns": turns,
               "evaluation": evaluation_function.__name__}
    return history, summary
