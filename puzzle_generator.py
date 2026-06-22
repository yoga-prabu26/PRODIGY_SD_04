"""
puzzle_generator.py
--------------------
Generates valid, uniquely-solvable Sudoku puzzles at four difficulty
levels: Easy, Medium, Hard, and Expert.

Generation strategy:
    1. Build a fully solved 9x9 grid using randomized backtracking.
    2. Iteratively remove digits (a "dig hole" strategy), at each step
       verifying with SudokuSolver.count_solutions() that the puzzle
       still has EXACTLY one solution. If removing a cell would create
       multiple solutions, the digit is put back and a different cell
       is tried.
    3. Stop once the target number of removed cells (per difficulty)
       is reached or no further safe removals are possible.
"""

from __future__ import annotations
import random
from enum import Enum
from typing import List, Tuple

from sudoku_solver import SudokuSolver, Grid, GRID_SIZE, BOX_SIZE, EMPTY


class Difficulty(Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    EXPERT = "Expert"


# Target number of EMPTY (removed) cells per difficulty.
# Standard Sudoku has 81 cells; higher difficulty = more blanks.
DIFFICULTY_BLANKS = {
    Difficulty.EASY: 36,     # ~45 givens
    Difficulty.MEDIUM: 46,   # ~35 givens
    Difficulty.HARD: 53,     # ~28 givens
    Difficulty.EXPERT: 58,   # ~23 givens
}


class PuzzleGenerator:
    """Generates new Sudoku puzzles paired with their solutions."""

    def __init__(self) -> None:
        self._solver = SudokuSolver()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(self, difficulty: Difficulty) -> Tuple[Grid, Grid]:
        """
        Generate a new puzzle for the given difficulty.

        Returns a tuple (puzzle, solution):
            puzzle   -> 9x9 grid with 0s representing blank cells
            solution -> the fully solved 9x9 grid
        """
        solution = self._generate_full_solution()
        puzzle = [row[:] for row in solution]
        blanks_target = DIFFICULTY_BLANKS[difficulty]
        puzzle = self._dig_holes(puzzle, blanks_target)
        return puzzle, solution

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _generate_full_solution(self) -> Grid:
        """
        Build a completely filled, valid 9x9 grid by randomized
        backtracking. Randomizing the order in which candidate values
        are tried ensures a different solved grid each time.
        """
        grid: Grid = [[EMPTY for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self._randomized_fill(grid, 0)
        return grid

    def _randomized_fill(self, grid: Grid, position: int) -> bool:
        if position == GRID_SIZE * GRID_SIZE:
            return True

        row, col = divmod(position, GRID_SIZE)
        values = list(range(1, 10))
        random.shuffle(values)

        for value in values:
            if SudokuSolver.is_valid_placement(grid, row, col, value):
                grid[row][col] = value
                if self._randomized_fill(grid, position + 1):
                    return True
                grid[row][col] = EMPTY

        return False

    def _dig_holes(self, grid: Grid, blanks_target: int) -> Grid:
        """
        Remove cells one at a time (in random order) while preserving
        uniqueness of the solution. Stops early if the target blank
        count cannot be safely reached.
        """
        all_cells: List[Tuple[int, int]] = [
            (r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)
        ]
        random.shuffle(all_cells)

        blanks_made = 0
        for row, col in all_cells:
            if blanks_made >= blanks_target:
                break

            removed_value = grid[row][col]
            if removed_value == EMPTY:
                continue

            grid[row][col] = EMPTY

            # Use a generous solver call limit (2) -- we only need to
            # know if there's more than one solution, not how many.
            solutions_found = self._solver.count_solutions(grid, limit=2)

            if solutions_found != 1:
                # Removing this cell broke uniqueness; restore it.
                grid[row][col] = removed_value
            else:
                blanks_made += 1

        return grid

    @staticmethod
    def grid_to_given_mask(puzzle: Grid) -> List[List[bool]]:
        """
        Returns a 9x9 boolean mask where True marks an original
        "given" cell (pre-filled, not user-editable) and False marks
        a cell the player must fill in.
        """
        return [[cell != EMPTY for cell in row] for row in puzzle]
