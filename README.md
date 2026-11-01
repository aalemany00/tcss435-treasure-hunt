# TCSS 435 - Treasure Hunt AI Project

A Python grid-world project in which an agent searches for treasure while
avoiding traps and static walls. The project is developed in phases, beginning
with the grid GUI and uninformed search (BFS, DFS, and UCS), followed by later
AI search and decision-making techniques.

## Team

| Name   | Role                                                                          |
|--------|-------------------------------------------------------------------------------|
| Adrian | GitHub setup, reset/regenerate functionality, README and submission packaging |
| Aramis | GUI rendering (colors, symbols, layout)                                       |
| Dylon  | Grid setup and random placement, updating REAMDME, fix minor bugs             |


## Requirements

- Python 3
- NumPy
- Pillow (PIL), if the GUI loads an image using `Image` and `ImageTk`
- Tkinter (normally included with standard Python distributions)

Install the third-party packages in the Python environment used by your IDE:  

```bash
python -m pip install numpy Pillow  
pip install numpy
```

## Project files

The main files are:

- `TreasureGridModel.py` — creates and stores the grid and the positions of
  the start, treasure, trap, and walls.
- `TreasureHuntGUI.py` — displays the grid, provides the algorithm buttons,
  and displays search results.
- `search.py` — contains the BFS, DFS, and UCS search implementations.
- `images/` — stores image assets used by the GUI, if applicable.

## Running the program

1. Open the project directory in your IDE or terminal.
2. Activate the project's virtual environment, if you use one.
3. Install the requirements listed above.
4. Run:

```bash
python TreasureHuntGUI.py
```

If your system uses `python3` instead of `python`, run:

```bash
python3 TreasureHuntGUI.py
```

Use **Run BFS**, **Run DFS**, or **Run UCS** to execute a search. Use
**Regenerate Grid** to create a new grid.

## Implementation and design

### Grid representation

The grid is represented as a two-dimensional NumPy array. Each cell's integer
value represents its type (for example, empty, start, wall, treasure, or trap).
Grid positions are represented as `(row, column)` coordinate pairs.

The grid model also keeps track of important positions, such as the start and
treasure, and stores wall positions in a set. The GUI reads the model's grid
and draws each cell with a distinct visual appearance.

### Search algorithms

The project implements three uninformed search algorithms:

- **Breadth-First Search (BFS):** explores the search frontier in
  first-in, first-out order. When all moves have equal cost, BFS finds a path
  with the fewest moves.
- **Depth-First Search (DFS):** explores one branch as far as possible before
  backtracking. It can find a solution, but it does not generally guarantee
  the path with the fewest moves.
- **Uniform-Cost Search (UCS):** expands the frontier position with the lowest
  accumulated path cost. It finds a least-cost path when step costs are
  nonnegative.

The search implementation should prevent revisiting already explored
positions, avoid trap and wall cells, and keep enough predecessor information
to reconstruct the path from the start to the treasure.

### Data structures

- **`deque` (BFS):** A FIFO queue that explores the grid level by level.
- **List (DFS):** Used as a LIFO stack; positions are popped from the end to
  explore one branch deeply before backtracking.
- **`heapq` (UCS):** A min-priority queue that expands the position with the
  lowest accumulated path cost.
- **Dictionaries:** Store each position's parent for path reconstruction.
  BFS also uses its parent dictionary to avoid revisiting positions; UCS uses
  dictionaries to track the lowest known cost and each position's parent.
- **Set (UCS):** Tracks positions that have already been expanded.
- **Tuples and lists:** `(row, column)` tuples identify grid positions, while
  lists hold DFS frontier entries and neighboring positions.

## Comparison of BFS, DFS, and UCS

### Experiments and Results (start is image at top left corner / (x, y) = (0, 0))
- Experiment 1:  

| Algorithm | Path cost | Nodes expanded | Runtime (sec) |
|-----------|----------:|---------------:|--------------:|
| BFS       |         8 |             29 |      2.434220 |
| DFS       |        14 |             23 |      1.925177 |
| UCS       |         8 |             33 |      2.780746 |  

<p>BFS</p>  
<img src = "/images/experiment_1_bfs.png" alt="">  
<p>DFS</p>  
<img src = "/images/experiment_1_dfs.png" alt="">  
<p>UCS</p>  
<img src = "/images/experiment_1_ucs.png" alt="">  

- Experiment 2:  

| Algorithm | Path cost | Nodes expanded | Runtime (sec) |
|-----------|----------:|---------------:|--------------:|
| BFS       |        18 |             94 |      7.916413 |
| DFS       |        60 |             84 |      7.072630 |
| UCS       |        18 |             94 |      7.925289 |  

<p>BFS</p>  
<img src = "/images/experiment_2_bfs.png" alt="">  
<p>DFS</p>  
<img src = "/images/experiment_2_dfs.png" alt="">  
<p>UCS</p>  
<img src = "/images/experiment_2_ucs.png" alt="">  

- Experiment 3:  

| Algorithm | Path cost | Nodes expanded | Runtime (sec) |
|-----------|----------:|---------------:|-------------:|
| BFS       |         9 |             47 |     3.958120 |
| DFS       |        47 |             60 |     5.056451 |
| UCS       |         9 |             40 |     3.357781 |  

<p>BFS</p>  
<img src = "/images/experiment_3_bfs.png" alt="">  
<p>DFS</p>  
<img src = "/images/experiment_3_dfs.png" alt="">  
<p>UCS</p>  
<img src = "/images/experiment_3_ucs.png" alt="">  
  
- Averages  

| Algorithm | Average Path cost | Average Nodes expanded | Avergae Runtime (sec) |
|-----------|------------------:|-----------------------:|---------------------:|
| DFS       |                40 |                     55 |             4.684753 |
| BFS       |                11 |                     56 |             4.769584 |
| UCS       |                11 |                     55 |             4.687939 |  


### Discussion of Results


- Which algorithm returned the lowest path cost?  
BFS and UCS always tied for path cost because, the cost of a path  
is always based on how many squares are traversed.  
  

- Which algorithm expanded the fewest nodes?  
  All three algorithms appeared to expand the same amount of nodes  
however, given the grid is only 10x10 the results are somewhat misleading.  
Further experimentation would be needed on much bigger grids to determine  
the differences in expanded nodes amongst BFS, DFS, and UCS.  


- Which algorithm had the shortest runtime?  
  Overall, DFS ran a bit shorter. This is rather misleading given that DFS with a much bigger  
grid should run slower but, because the grid is 10x10 the runtime seems trivial  
since all three algorithms do not need to traverse much to find the treasure.

## Sample GUI screenshot

![Grid with a sample search result highlighted](/images/sample_gui_result.png)


## Generative AI Statement

1. What was used: ChatGPT  
How it was used: to make png image appear on the start position  
Which parts of the work are original vs. AI-assisted: lines 45-46 and 4-5  
for importing appropriate libs and loading and sizing image.  
2. What was used: ChatGPT  
How it was used: help with resizing increasing grid sizes 10x10, 20x20 and bigger  
to help make the view of the grid not take up too much space so that buttons are  
still accessible.

## Workflow

- Keep `main` working and mergeable.
- Work on separate feature branches and open pull requests into `main`.
- Have at least one other teammate review changes before merging.

## Sources
- image used for start position here: [https://pixar.fandom.com/wiki/Geri](https://pixar.fandom.com/wiki/Geri)
