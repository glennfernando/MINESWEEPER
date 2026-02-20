from engine.game import GameEngine
from typing import List, Tuple, Dict, Set
import random

class AIAgent:
    def __init__(self, game: GameEngine):
        self.game = game
        self.probabilities: Dict[Tuple[int, int], float] = {}
        
    def get_frontier(self):
        """Finds all revealed numbers that border unrevealed cells and all unrevealed cells that border revealed numbers."""
        revealed_numbers = set()
        frontier_unrevealed = set()
        
        for r in range(self.game.rows):
            for c in range(self.game.cols):
                cell = self.game.cells[(r, c)]
                if cell.is_revealed and cell.neighbor_mines > 0:
                    unrevealed_neighbors = []
                    for nr, nc in self.game.get_neighbors(r, c):
                        n = self.game.cells[(nr, nc)]
                        if not n.is_revealed and not n.is_flagged:
                            unrevealed_neighbors.append((nr, nc))
                    
                    if unrevealed_neighbors:
                        revealed_numbers.add((r, c))
                        for n_coord in unrevealed_neighbors:
                            frontier_unrevealed.add(n_coord)
                            
        return list(revealed_numbers), list(frontier_unrevealed)

    def separate_components(self, revealed_numbers: List[Tuple[int, int]], frontier_unrevealed: List[Tuple[int, int]]):
        """Separates the frontier into independent regions."""
        # This simplifies inference drastically.
        # Two unrevealed cells are connected if they share a revealed number constraint.
        components = []
        unassigned = set(frontier_unrevealed)
        
        # Build adjacency: unrevealed -> numbers it affects
        cell_to_numbers = {u: set() for u in frontier_unrevealed}
        number_to_cells = {n: set() for n in revealed_numbers}
        
        for r, c in revealed_numbers:
            for nr, nc in self.game.get_neighbors(r, c):
                if (nr, nc) in unassigned:
                    cell_to_numbers[(nr, nc)].add((r, c))
                    number_to_cells[(r, c)].add((nr, nc))
                    
        while unassigned:
            start = unassigned.pop()
            comp_cells = {start}
            comp_numbers = set(cell_to_numbers[start])
            
            queue = [start]
            while queue:
                curr = queue.pop(0)
                for num in cell_to_numbers[curr]:
                    comp_numbers.add(num)
                    for neighbor_cell in number_to_cells[num]:
                        if neighbor_cell in unassigned:
                            unassigned.remove(neighbor_cell)
                            comp_cells.add(neighbor_cell)
                            queue.append(neighbor_cell)
            
            components.append((list(comp_cells), list(comp_numbers)))
            
        return components

    def calculate_probabilities(self):
        self.probabilities.clear()
        
        if self.game.first_click:
            # All probabilities are zero/uniform initially
            return
            
        revealed_numbers, frontier_unrevealed = self.get_frontier()
        components = self.separate_components(revealed_numbers, frontier_unrevealed)
        
        # Keep track of total mine configurations used per component to compute global probabilties later if needed,
        # but for simple independent regions we can assume local probability = global probability for that region.
        
        total_mines_placed = sum(1 for c in self.game.cells.values() if c.is_flagged)
        
        for comp_cells, comp_numbers in components:
            cell_to_idx = {cell: i for i, cell in enumerate(comp_cells)}
            number_constraints = []
            
            for r, c in comp_numbers:
                cell = self.game.cells[(r, c)]
                base_flags = 0
                unassigned_indices = []
                for nr, nc in self.game.get_neighbors(r, c):
                    n_cell = self.game.cells[(nr, nc)]
                    if n_cell.is_flagged:
                        base_flags += 1
                    elif (nr, nc) in cell_to_idx:
                        unassigned_indices.append(cell_to_idx[(nr, nc)])
                
                target = cell.neighbor_mines - base_flags
                number_constraints.append((target, unassigned_indices))

            valid_configs = []
            current_config = [None] * len(comp_cells)
            
            def dfs(idx):
                for target, indices in number_constraints:
                    mines = 0
                    unassigned = 0
                    for c_idx in indices:
                        val = current_config[c_idx]
                        if val is True:
                            mines += 1
                        elif val is None:
                            unassigned += 1
                            
                    if mines > target or mines + unassigned < target:
                        return
                        
                if idx == len(comp_cells):
                    valid_configs.append(current_config.copy())
                    return
                
                current_config[idx] = True
                dfs(idx + 1)
                
                current_config[idx] = False
                dfs(idx + 1)
                
                current_config[idx] = None
                
            dfs(0)
            
            if not valid_configs:
                continue
                
            total_configs = len(valid_configs)
            for i, cell in enumerate(comp_cells):
                mine_count = sum(1 for conf in valid_configs if conf[i])
                self.probabilities[cell] = mine_count / total_configs
                
        # Calculate background probability for non-frontier cells
        remaining_mines = self.game.total_mines - total_mines_placed
        unrevealed_all = [(r, c) for r in range(self.game.rows) for c in range(self.game.cols) 
                          if not self.game.cells[(r, c)].is_revealed and not self.game.cells[(r, c)].is_flagged]
        
        background_cells = [c for c in unrevealed_all if c not in self.probabilities]
        
        if background_cells:
            # This is a simplification: assuming local component solutions don't bottleneck the global mine count.
            # A full PGM would cross-reference component states with the global total_mines constraint.
            expected_frontier_mines = sum(self.probabilities[c] for c in frontier_unrevealed)
            remaining_bg_mines = max(0, remaining_mines - expected_frontier_mines)
            bg_prob = min(1.0, remaining_bg_mines / len(background_cells))
            
            for c in background_cells:
                self.probabilities[c] = bg_prob

    def step(self):
        if self.game.game_over or self.game.victory:
            return None

        if self.game.first_click:
            # guess center
            r = self.game.rows // 2
            c = self.game.cols // 2
            return ('reveal', r, c)
            
        self.calculate_probabilities()
        
        # 1. Deterministic moves
        for c, prob in self.probabilities.items():
            if prob == 1.0 and not self.game.cells[c].is_flagged:
                return ('flag', c[0], c[1])
            elif prob == 0.0 and not self.game.cells[c].is_revealed:
                return ('reveal', c[0], c[1])
                
        # 2. Probabilistic Guess
        if not self.probabilities:
            # Fallback (shouldn't happen unless stuck)
            unrevealed = [(r, c) for r in range(self.game.rows) for c in range(self.game.cols) 
                          if not self.game.cells[(r, c)].is_revealed and not self.game.cells[(r, c)].is_flagged]
            if unrevealed:
                c = random.choice(unrevealed)
                return ('reveal', c[0], c[1])
            return None
            
        # Find minimum probability > 0 (as 0s are already handled)
        # However if there are only high probs left, min is fine
        min_prob = min(self.probabilities.values())
        best_cells = [c for c, p in self.probabilities.items() if p == min_prob]
        
        choice = random.choice(best_cells)
        return ('reveal', choice[0], choice[1])
