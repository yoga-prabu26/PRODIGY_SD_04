"""
validator.py
-------------
Validation logic for SudokuMaster Pro.

Separated from the solver because validation concerns the CURRENT
state of a user's in-progress board (e.g. "did the player make a
mistake?", "is the board complete and correct?") whereas the solver
concerns finding/counting solutions.
"""

from __future__ import annotations
from typing import List, Tuple

from sudoku_solver import Grid, GRID_SIZE, BOX_SIZE, EMPTY


class ValidationResult:
    """Simple value object describing the outcome of a validation check."""

    def __init__(self, is_valid: bool, conflicts: List[Tuple[int, int]]) -> None:
        self.is_valid = is_valid
        # List of (row, col) cells that conflict with the placed value.
        self.conflicts = conflicts

    def __bool__(self) -> bool:
        return self.is_valid


class SudokuValidator:
    """Stateless helper class for validating Sudoku board state."""

    @staticmethod
    def find_conflicts(grid: Grid, row: int, col: int) -> List[Tuple[int, int]]:
        """
        Given a filled cell at (row, col), return every OTHER cell in
        its row, column, or box that shares the same non-zero value
        (i.e. a rule violation involving this cell).
        """
        value = grid[row][col]
        conflicts: List[Tuple[int, int]] = []
        if value == EMPTY:
            return conflicts

        for c in range(GRID_SIZE):
            if c != col and grid[row][c] == value:
                conflicts.append((row, c))
        for r in range(GRID_SIZE):
            if r != row and grid[r][col] == value:
                conflicts.append((r, col))

        box_row, box_col = (row // BOX_SIZE) * BOX_SIZE, (col // BOX_SIZE) * BOX_SIZE
        for r in range(box_row, box_row + BOX_SIZE):
            for c in range(box_col, box_col + BOX_SIZE):
                if (r, c) != (row, col) and grid[r][c] == value and (r, c) not in conflicts:
                    conflicts.append((r, c))

        return conflicts

    @staticmethod
    def validate_move(grid: Grid, row: int, col: int) -> ValidationResult:
        """Check whether the value currently at (row, col) is legal."""
        conflicts = SudokuValidator.find_conflicts(grid, row, col)
        return ValidationResult(is_valid=(len(conflicts) == 0), conflicts=conflicts)

    @staticmethod
    def is_move_correct(value: int, row: int, col: int, solution: Grid) -> bool:
        """
        Compare a user's entered value against the known solution.
        Used for "mistake detection" / auto-check mode.
        """
        return solution[row][col] == value

    @staticmethod
    def is_board_complete(grid: Grid) -> bool:
        """True if every cell is filled (no zeros remain)."""
        return all(cell != EMPTY for row in grid for cell in row)

    @staticmethod
    def is_board_correct(grid: Grid, solution: Grid) -> bool:
        """True if the board exactly matches the known solution."""
        return grid == solution

    @staticmethod
    def completion_percentage(grid: Grid, given_mask: List[List[bool]]) -> float:
        """
        Percentage of PLAYER-FILLABLE cells that currently hold a
        value (givens are excluded from the denominator since the
        player didn't fill those in).
        """
        fillable = 0
        filled = 0
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if not given_mask[r][c]:
                    fillable += 1
                    if grid[r][c] != EMPTY:
                        filled += 1
        if fillable == 0:
            return 100.0
        return round((filled / fillable) * 100, 1)

    @staticmethod
    def count_mistakes(grid: Grid, solution: Grid, given_mask: List[List[bool]]) -> int:
        """
        Count how many player-filled cells currently hold a value
        that does not match the solution.
        """
        mistakes = 0
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if not given_mask[r][c] and grid[r][c] != EMPTY:
                    if grid[r][c] != solution[r][c]:
                        mistakes += 1
        return mistakes
