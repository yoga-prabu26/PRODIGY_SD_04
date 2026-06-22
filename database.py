"""
database.py
------------
SQLite persistence layer for SudokuMaster Pro.

Stores completed/abandoned game records for the History window and
Statistics Dashboard. Keeping all DB access behind this one class
means the rest of the app never writes raw SQL.
"""

from __future__ import annotations
import sqlite3
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sudoku_master_pro.db")


@dataclass
class GameRecord:
    """Represents a single row in the games history table."""
    id: Optional[int]
    difficulty: str
    duration_seconds: int
    moves: int
    hints_used: int
    mistakes: int
    completed: bool
    completion_percent: float
    played_at: str  # ISO formatted timestamp


class Database:
    """Thin wrapper around sqlite3 for SudokuMaster Pro's persistence needs."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self._initialize_schema()

    # ------------------------------------------------------------------
    # Schema setup
    # ------------------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    difficulty TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    moves INTEGER NOT NULL,
                    hints_used INTEGER NOT NULL,
                    mistakes INTEGER NOT NULL,
                    completed INTEGER NOT NULL,
                    completion_percent REAL NOT NULL,
                    played_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------
    def record_game(self, record: GameRecord) -> int:
        """Insert a new game record and return its new row id."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO games
                    (difficulty, duration_seconds, moves, hints_used,
                     mistakes, completed, completion_percent, played_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.difficulty,
                    record.duration_seconds,
                    record.moves,
                    record.hints_used,
                    record.mistakes,
                    1 if record.completed else 0,
                    record.completion_percent,
                    record.played_at,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------
    def fetch_all_games(self) -> List[GameRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM games ORDER BY played_at DESC"
            ).fetchall()
            return [self._row_to_record(row) for row in rows]

    def search_games(
        self,
        difficulty: Optional[str] = None,
        completed_only: bool = False,
        keyword: Optional[str] = None,
    ) -> List[GameRecord]:
        """
        Search history with optional filters. `keyword` matches loosely
        against difficulty and the played_at date string, which is
        sufficient for a lightweight searchable history window.
        """
        query = "SELECT * FROM games WHERE 1=1"
        params: list = []

        if difficulty and difficulty != "All":
            query += " AND difficulty = ?"
            params.append(difficulty)

        if completed_only:
            query += " AND completed = 1"

        if keyword:
            query += " AND (difficulty LIKE ? OR played_at LIKE ?)"
            like_term = f"%{keyword}%"
            params.extend([like_term, like_term])

        query += " ORDER BY played_at DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_record(row) for row in rows]

    def get_statistics(self) -> dict:
        """
        Compute aggregate statistics across all stored games:
        total games, completed games, best time per difficulty,
        average completion percent, total hints used.
        """
        games = self.fetch_all_games()
        stats = {
            "total_games": len(games),
            "completed_games": sum(1 for g in games if g.completed),
            "total_hints_used": sum(g.hints_used for g in games),
            "average_completion": 0.0,
            "best_time_by_difficulty": {},
        }

        if games:
            stats["average_completion"] = round(
                sum(g.completion_percent for g in games) / len(games), 1
            )

        for difficulty in ("Easy", "Medium", "Hard", "Expert"):
            completed_games = [
                g for g in games if g.difficulty == difficulty and g.completed
            ]
            if completed_games:
                best = min(g.duration_seconds for g in completed_games)
                stats["best_time_by_difficulty"][difficulty] = best

        return stats

    def clear_history(self) -> None:
        """Delete all stored game records (used by a 'clear history' action)."""
        with self._connect() as conn:
            conn.execute("DELETE FROM games")
            conn.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> GameRecord:
        return GameRecord(
            id=row["id"],
            difficulty=row["difficulty"],
            duration_seconds=row["duration_seconds"],
            moves=row["moves"],
            hints_used=row["hints_used"],
            mistakes=row["mistakes"],
            completed=bool(row["completed"]),
            completion_percent=row["completion_percent"],
            played_at=row["played_at"],
        )

    @staticmethod
    def now_iso() -> str:
        return datetime.now().isoformat(timespec="seconds")
