import random
from typing import List, Tuple, Dict, Set

class Cell:
    def __init__(self, r: int, c: int):
        self.r = r
        self.c = c
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False
        self.neighbor_mines = 0

class GameEngine:
    LEVELS = {
        'beginner': {'rows': 9, 'cols': 9, 'mines': 10},
        'intermediate': {'rows': 16, 'cols': 16, 'mines': 40},
        'expert': {'rows': 16, 'cols': 30, 'mines': 99},
        'professional': {'rows': 30, 'cols': 30, 'mines': 200},
    }

    def __init__(self, level='intermediate', shape='square'):
        self.level = level
        self.shape = shape
        self.rows = self.LEVELS[level]['rows']
        self.cols = self.LEVELS[level]['cols']
        self.total_mines = self.LEVELS[level]['mines']
        self.cells: Dict[Tuple[int, int], Cell] = {}
        self.first_click = True
        self.game_over = False
        self.victory = False
        self.reset()

    def reset(self):
        self.cells = {}
        for r in range(self.rows):
            for c in range(self.cols):
                self.cells[(r, c)] = Cell(r, c)
        self.first_click = True
        self.game_over = False
        self.victory = False

    def get_neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        neighbors = []
        if self.shape == 'square':
            dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    neighbors.append((nr, nc))
        elif self.shape == 'hexagon':
            # "odd-r" horizontal layout
            dirs_even = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
            dirs_odd = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
            dirs = dirs_odd if r % 2 != 0 else dirs_even
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    neighbors.append((nr, nc))
        return neighbors

    def place_mines(self, safe_r: int, safe_c: int):
        safe_zone = self.get_neighbors(safe_r, safe_c)
        safe_zone.append((safe_r, safe_c))
        
        all_coords = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        valid_coords = [coord for coord in all_coords if coord not in safe_zone]
        
        # In rare cases, the safe zone might be too big for the number of mines
        # Just ensure starting cell block is always 0
        if len(valid_coords) < self.total_mines:
            valid_coords = [coord for coord in all_coords if coord != (safe_r, safe_c)]
            
        mine_coords = random.sample(valid_coords, self.total_mines)
        
        for coord in mine_coords:
            self.cells[coord].is_mine = True

        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells[(r, c)]
                if not cell.is_mine:
                    mines_around = sum(1 for nr, nc in self.get_neighbors(r, c) if self.cells[(nr, nc)].is_mine)
                    cell.neighbor_mines = mines_around

    def reveal(self, r: int, c: int):
        if self.game_over or self.victory:
            return
            
        cell = self.cells.get((r, c))
        if not cell or cell.is_revealed or cell.is_flagged:
            return

        if self.first_click:
            self.place_mines(r, c)
            self.first_click = False

        if cell.is_mine:
            cell.is_revealed = True
            self.game_over = True
            return

        # Flood fill reveal
        stack = [(r, c)]
        while stack:
            curr_r, curr_c = stack.pop()
            curr_cell = self.cells[(curr_r, curr_c)]
            
            if not curr_cell.is_revealed and not curr_cell.is_flagged:
                curr_cell.is_revealed = True
                if curr_cell.neighbor_mines == 0:
                    for nr, nc in self.get_neighbors(curr_r, curr_c):
                        stack.append((nr, nc))
                        
        self.check_victory()

    def toggle_flag(self, r: int, c: int):
        if self.game_over or self.victory:
            return
            
        cell = self.cells.get((r, c))
        if cell and not cell.is_revealed:
            cell.is_flagged = not cell.is_flagged

    def check_victory(self):
        revealed_count = sum(1 for c in self.cells.values() if c.is_revealed)
        total_safe = (self.rows * self.cols) - self.total_mines
        if revealed_count == total_safe:
            self.victory = True

    def toggle_chord(self, r: int, c: int):
        # Middle click logic (Chording)
        if self.game_over or self.victory:
            return
            
        cell = self.cells.get((r, c))
        if not cell or not cell.is_revealed:
            return
            
        flags_around = sum(1 for nr, nc in self.get_neighbors(r, c) if self.cells[(nr, nc)].is_flagged)
        if flags_around == cell.neighbor_mines:
            for nr, nc in self.get_neighbors(r, c):
                n_cell = self.cells[(nr, nc)]
                if not n_cell.is_revealed and not n_cell.is_flagged:
                    self.reveal(nr, nc)
