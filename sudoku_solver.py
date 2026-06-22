"""
sudoku_solver.py
-----------------
Core solving engine for SudokuMaster Pro.

Implements a constraint-propagation backtracking solver that uses the
Minimum Remaining Values (MRV) heuristic to choose which empty cell to
fill next. This dramatically reduces the search space compared to a
naive left-to-right backtracking solver, especially on Hard/Expert
puzzles.

The module is intentionally independent of any UI code so it can be
unit tested or reused in other contexts (CLI tools, tests, etc.).
"""

from __future__ import annotations
from typing import List, Optional, Set, Tuple

Grid = List[List[int]]

GRID_SIZE = 9
BOX_SIZE = 3
EMPTY = 0


class SudokuSolver:
    """
    Encapsulates all logic required to solve a 9x9 Sudoku grid.

    A grid is represented as a list of 9 lists of 9 integers, where 0
    denotes an empty cell and 1-9 denote filled values.
    """

    def __init__(self) -> None:
        self._nodes_explored = 0  # Diagnostic counter, useful for stats.

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def solve(self, grid: Grid) -> bool:
        """
        Solve the given grid in place using backtracking + MRV.

        Returns True if a solution was found (the grid is mutated to
        contain the solution), False if the grid is unsolvable.
        """
        self._nodes_explored = 0
        candidates = self._build_candidate_map(grid)
        return self._backtrack(grid, candidates)

    def get_solution(self, grid: Grid) -> Optional[Grid]:
        """
        Return a solved copy of `grid` without mutating the original.
        Returns None if no solution exists.
        """
        working_copy = [row[:] for row in grid]
        if self.solve(working_copy):
            return working_copy
        return None

    def count_solutions(self, grid: Grid, limit: int = 2) -> int:
        """
        Count how many solutions a grid has, stopping early once
        `limit` is reached. This is primarily used by the puzzle
        generator to guarantee uniqueness (limit=2 is enough to know
        "more than one solution exists" without solving exhaustively).
        """
        working_copy = [row[:] for row in grid]
        candidates = self._build_candidate_map(working_copy)
        counter = {"count": 0}
        self._count_backtrack(working_copy, candidates, counter, limit)
        return counter["count"]

    def is_solvable(self, grid: Grid) -> bool:
        """Quick check: does at least one solution exist?"""
        return self.get_solution(grid) is not None

    def nodes_explored(self) -> int:
        """Return the number of recursive calls made during last solve()."""
        return self._nodes_explored

    @staticmethod
    def get_box_index(row: int, col: int) -> int:
        """Return the index (0-8) of the 3x3 box containing (row, col)."""
        return (row // BOX_SIZE) * BOX_SIZE + (col // BOX_SIZE)

    @staticmethod
    def is_valid_placement(grid: Grid, row: int, col: int, value: int) -> bool:
        """
        Check whether placing `value` at (row, col) violates Sudoku
        rules against the CURRENT state of `grid` (row/col/box).
        Assumes grid[row][col] is currently empty or will be ignored.
        """
        for c in range(GRID_SIZE):
            if c != col and grid[row][c] == value:
                return False
        for r in range(GRID_SIZE):
            if r != row and grid[r][col] == value:
                return False
        box_row, box_col = (row // BOX_SIZE) * BOX_SIZE, (col // BOX_SIZE) * BOX_SIZE
        for r in range(box_row, box_row + BOX_SIZE):
            for c in range(box_col, box_col + BOX_SIZE):
                if (r, c) != (row, col) and grid[r][c] == value:
                    return False
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_candidate_map(self, grid: Grid) -> List[List[Set[int]]]:
        """
        Build a 9x9 map where each empty cell holds the set of legal
        candidate values, given the current grid state. Filled cells
        get an empty set (unused).
        """
        candidates: List[List[Set[int]]] = [
            [set() for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)
        ]
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if grid[row][col] == EMPTY:
                    candidates[row][col] = self._legal_values(grid, row, col)
        return candidates

    def _legal_values(self, grid: Grid, row: int, col: int) -> Set[int]:
        used: Set[int] = set()
        for c in range(GRID_SIZE):
            used.add(grid[row][c])
        for r in range(GRID_SIZE):
            used.add(grid[r][col])
        box_row, box_col = (row // BOX_SIZE) * BOX_SIZE, (col // BOX_SIZE) * BOX_SIZE
        for r in range(box_row, box_row + BOX_SIZE):
            for c in range(box_col, box_col + BOX_SIZE):
                used.add(grid[r][c])
        return {v for v in range(1, 10) if v not in used}

    def _find_mrv_cell(
        self, grid: Grid, candidates: List[List[Set[int]]]
    ) -> Optional[Tuple[int, int]]:
        """
        Find the empty cell with the fewest legal candidates (Minimum
        Remaining Values). Returns None if the grid is fully filled.
        """
        best_cell: Optional[Tuple[int, int]] = None
        best_count = 10
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if grid[row][col] == EMPTY:
                    count = len(candidates[row][col])
                    if count < best_count:
                        best_count = count
                        best_cell = (row, col)
                        if best_count == 0:
                            # Dead end found early; no point searching further.
                            return best_cell
        return best_cell

    def _update_peers(
        self, candidates: List[List[Set[int]]], row: int, col: int, value: int, remove: bool
    ) -> List[Tuple[int, int]]:
        """
        Add or remove `value` from the candidate sets of every peer
        (same row, column, box) of (row, col). Returns the list of
        peer cells that were actually modified, so the caller can
        undo the change efficiently on backtrack.
        """
        touched: List[Tuple[int, int]] = []

        def touch(r: int, c: int) -> None:
            cell_set = candidates[r][c]
            if remove:
                if value in cell_set:
                    cell_set.discard(value)
                    touched.append((r, c))
            else:
                if (r, c) not in touched:
                    cell_set.add(value)

        for c in range(GRID_SIZE):
            if c != col:
                touch(row, c)
        for r in range(GRID_SIZE):
            if r != row:
                touch(r, col)
        box_row, box_col = (row // BOX_SIZE) * BOX_SIZE, (col // BOX_SIZE) * BOX_SIZE
        for r in range(box_row, box_row + BOX_SIZE):
            for c in range(box_col, box_col + BOX_SIZE):
                if (r, c) != (row, col):
                    touch(r, c)
        return touched

    def _backtrack(self, grid: Grid, candidates: List[List[Set[int]]]) -> bool:
        self._nodes_explored += 1
        cell = self._find_mrv_cell(grid, candidates)
        if cell is None:
            return True  # No empty cells left -> solved.

        row, col = cell
        cell_candidates = candidates[row][col]
        if not cell_candidates:
            return False  # Dead end.

        for value in sorted(cell_candidates):
            grid[row][col] = value
            removed_from = self._update_peers(candidates, row, col, value, remove=True)
            original_set = candidates[row][col]
            candidates[row][col] = set()

            if self._backtrack(grid, candidates):
                return True

            # Undo.
            candidates[row][col] = original_set
            for r, c in removed_from:
                candidates[r][c].add(value)
            grid[row][col] = EMPTY

        return False

    def _count_backtrack(
        self,
        grid: Grid,
        candidates: List[List[Set[int]]],
        counter: dict,
        limit: int,
    ) -> None:
        if counter["count"] >= limit:
            return

        cell = self._find_mrv_cell(grid, candidates)
        if cell is None:
            counter["count"] += 1
            return

        row, col = cell
        cell_candidates = candidates[row][col]
        if not cell_candidates:
            return

        for value in sorted(cell_candidates):
            if counter["count"] >= limit:
                return
            grid[row][col] = value
            removed_from = self._update_peers(candidates, row, col, value, remove=True)
            original_set = candidates[row][col]
            candidates[row][col] = set()

            self._count_backtrack(grid, candidates, counter, limit)

            candidates[row][col] = original_set
            for r, c in removed_from:
                candidates[r][c].add(value)
            grid[row][col] = EMPTY
