# Minesweeper AI Agent

An intelligent Minesweeper implementation built in Python, featuring a custom game engine and an AI agent capable of mathematically solving boards using concepts from Probabilistic Graphical Models (PGM) and quantitative analysis.

## Demo

![Demo](DEMO.mp4)

## Core Features

- **Advanced AI Solver**: Automatically calculates safe moves and probable mine locations by isolating the unrevealed frontier into independent sub-regions and computing valid permutations.
- **Standard & Extended Difficulties**: Play on Beginner (9x9), Intermediate (16x16), Expert (30x16), and Professional (30x30) modes.
- **First-Click Guaranteed Safe**: The game dynamically generates the minefield *after* your initial click, guaranteeing an open start.
- **Multiple Grid Topologies**: Engine calculates neighbor relationships dynamically, supporting both traditional Square boards and experimental Hexagonal grids.

## AI Architecture & Optimizations

The AI Agent acts as a specialized probability engine designed directly for the constraints of Minesweeper:

1. **Frontier Extraction**: It identifies the boundary between the revealed safe cells (constraints) and the surrounding unrevealed cells.
2. **Component Separation**: To avoid calculating permutations for the entire board simultaneously, it splits disjoint frontier areas into independent mathematical sub-graphs. This massively reduces computational complexity.
3. **Constraint Satisfaction DFS**: It iterates through all valid mine permutations for each independent region. 
    - *Optimization applied*: The calculation algorithm is highly optimized to pre-compute local target requirements before evaluating permutations, dodging hundreds of redundant state lookups recursively.
4. **Action Selection**: 
    - Executes deterministic maneuvers for guaranteed mines (100% Probability -> Flag) and guaranteed safe spaces (0% Probability -> Reveal).
    - When forced to guess, it queries the PGM probability map, picking the cell with the lowest computed likelihood of containing a mine.

## Running the Project

Ensure you have Python 3 installed.

```bash
cd MINESWEEPER
python3 main.py
```
