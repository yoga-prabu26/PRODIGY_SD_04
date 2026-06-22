"""
save_manager.py
-----------------
Handles persisting the in-progress game state to disk (Save Game /
Load Game) and exporting a puzzle for sharing (Export Puzzle).

Saves are stored as JSON under saves/ and exports under exports/, so
the project folder doubles as a tidy demonstration of file I/O and
JSON handling for portfolio review.
"""

from __future__ import annotations
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from sudoku_solver import Grid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVES_DIR = os.path.join(BASE_DIR, "saves")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")


class SaveManager:
    """Reads/writes JSON snapshots of game state for save/load/export."""

    def __init__(self) -> None:
        os.makedirs(SAVES_DIR, exist_ok=True)
        os.makedirs(EXPORTS_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # Save / Load (full game state, resumable)
    # ------------------------------------------------------------------
    def save_game(
        self,
        puzzle: Grid,
        solution: Grid,
        given_mask: List[List[bool]],
        difficulty: str,
        elapsed_seconds: int,
        moves: int,
        hints_used: int,
        filename: Optional[str] = None,
    ) -> str:
        """
        Serialize the full game state to a JSON file so the player can
        resume later. Returns the absolute path written.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sudoku_save_{difficulty.lower()}_{timestamp}.json"

        if not filename.endswith(".json"):
            filename += ".json"

        payload: Dict[str, Any] = {
            "version": 1,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "difficulty": difficulty,
            "puzzle": puzzle,
            "solution": solution,
            "given_mask": given_mask,
            "elapsed_seconds": elapsed_seconds,
            "moves": moves,
            "hints_used": hints_used,
        }

        full_path = os.path.join(SAVES_DIR, filename)
        with open(full_path, "w", encoding="utf-8") as file_handle:
            json.dump(payload, file_handle, indent=2)

        return full_path

    def load_game(self, file_path: str) -> Dict[str, Any]:
        """
        Load a previously saved game. Raises FileNotFoundError or
        json.JSONDecodeError on malformed input, which the caller
        (UI layer) is expected to catch and present as a friendly
        error dialog.
        """
        with open(file_path, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)

        required_keys = {"puzzle", "solution", "given_mask", "difficulty"}
        if not required_keys.issubset(data.keys()):
            raise ValueError("Save file is missing required fields.")

        return data

    def list_saves(self) -> List[str]:
        """Return absolute paths of all .json save files, newest first."""
        if not os.path.isdir(SAVES_DIR):
            return []
        files = [
            os.path.join(SAVES_DIR, name)
            for name in os.listdir(SAVES_DIR)
            if name.endswith(".json")
        ]
        files.sort(key=os.path.getmtime, reverse=True)
        return files

    # ------------------------------------------------------------------
    # Export (puzzle only, for sharing -- no solution embedded)
    # ------------------------------------------------------------------
    def export_puzzle(
        self, puzzle: Grid, difficulty: str, file_format: str = "json"
    ) -> str:
        """
        Export just the puzzle (not the solution or progress) so it
        can be shared or archived. Supports 'json' and 'txt' formats.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"sudoku_export_{difficulty.lower()}_{timestamp}"

        if file_format == "txt":
            full_path = os.path.join(EXPORTS_DIR, base_name + ".txt")
            with open(full_path, "w", encoding="utf-8") as file_handle:
                file_handle.write(f"SudokuMaster Pro -- Puzzle Export\n")
                file_handle.write(f"Difficulty: {difficulty}\n")
                file_handle.write(f"Exported: {datetime.now().isoformat(timespec='seconds')}\n\n")
                for row in puzzle:
                    line = " ".join(str(v) if v != 0 else "." for v in row)
                    file_handle.write(line + "\n")
        else:
            full_path = os.path.join(EXPORTS_DIR, base_name + ".json")
            payload = {
                "difficulty": difficulty,
                "exported_at": datetime.now().isoformat(timespec="seconds"),
                "puzzle": puzzle,
            }
            with open(full_path, "w", encoding="utf-8") as file_handle:
                json.dump(payload, file_handle, indent=2)

        return full_path
