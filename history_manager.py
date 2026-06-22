"""
history_manager.py
--------------------
Implements the History window: a Toplevel that lists past games
pulled from the SQLite database, with search/filter controls and a
small statistics summary at the top.
"""

from __future__ import annotations
import customtkinter as ctk
from typing import Optional

from database import Database
from theme_manager import ThemeManager


class HistoryWindow(ctk.CTkToplevel):
    """A searchable, filterable window showing past Sudoku games."""

    def __init__(self, master, database: Database, theme: ThemeManager) -> None:
        super().__init__(master)
        self.database = database
        self.theme = theme
        palette = self.theme.palette

        self.title("Game History — SudokuMaster Pro")
        self.geometry("900x600")
        self.minsize(700, 450)
        self.configure(fg_color=palette.background)

        self._build_layout()
        self._populate(self.database.fetch_all_games())

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        palette = self.theme.palette

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="Game History",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=palette.text,
        ).pack(side="left")

        self.stats_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=palette.text_muted,
        )
        self.stats_label.pack(side="right")

        # --- Search / filter bar -----------------------------------
        controls = ctk.CTkFrame(self, fg_color=palette.card, corner_radius=10)
        controls.pack(fill="x", padx=20, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            controls, placeholder_text="Search by date or keyword...", width=280
        )
        self.search_entry.pack(side="left", padx=12, pady=12)
        self.search_entry.bind("<Return>", lambda _event: self._on_search())

        self.difficulty_filter = ctk.CTkOptionMenu(
            controls,
            values=["All", "Easy", "Medium", "Hard", "Expert"],
            width=140,
        )
        self.difficulty_filter.pack(side="left", padx=8, pady=12)

        self.completed_only_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            controls,
            text="Completed only",
            variable=self.completed_only_var,
            command=self._on_search,
        ).pack(side="left", padx=8, pady=12)

        ctk.CTkButton(
            controls, text="Search", width=90, command=self._on_search
        ).pack(side="left", padx=8, pady=12)

        ctk.CTkButton(
            controls,
            text="Clear Filters",
            width=110,
            fg_color="transparent",
            border_width=1,
            text_color=palette.text,
            command=self._on_clear_filters,
        ).pack(side="left", padx=8, pady=12)

        ctk.CTkButton(
            controls,
            text="Clear History",
            width=110,
            fg_color=palette.danger,
            hover_color="#B91C1C",
            command=self._on_clear_history,
        ).pack(side="right", padx=12, pady=12)

        # --- Scrollable results list --------------------------------
        self.results_frame = ctk.CTkScrollableFrame(
            self, fg_color=palette.card, corner_radius=10
        )
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Column headers
        self._add_row(
            self.results_frame,
            ["Date", "Difficulty", "Time", "Moves", "Hints", "Mistakes", "Status"],
            header=True,
        )

    # ------------------------------------------------------------------
    # Data population
    # ------------------------------------------------------------------
    def _populate(self, games) -> None:
        palette = self.theme.palette

        # Remove all rows except the header (index 0).
        children = self.results_frame.winfo_children()
        for child in children[1:]:
            child.destroy()

        if not games:
            empty_label = ctk.CTkLabel(
                self.results_frame,
                text="No games found. Play a puzzle to build your history!",
                text_color=palette.text_muted,
            )
            empty_label.pack(pady=30)
        else:
            for game in games:
                minutes, seconds = divmod(game.duration_seconds, 60)
                time_str = f"{minutes:02d}:{seconds:02d}"
                status = "✓ Completed" if game.completed else "Incomplete"
                date_str = game.played_at.replace("T", "  ")
                self._add_row(
                    self.results_frame,
                    [
                        date_str,
                        game.difficulty,
                        time_str,
                        str(game.moves),
                        str(game.hints_used),
                        str(game.mistakes),
                        status,
                    ],
                    success=game.completed,
                )

        stats = self.database.get_statistics()
        best_times = ", ".join(
            f"{difficulty}: {seconds // 60}m {seconds % 60}s"
            for difficulty, seconds in stats["best_time_by_difficulty"].items()
        ) or "No completed games yet"
        self.stats_label.configure(
            text=(
                f"Total games: {stats['total_games']}  |  "
                f"Completed: {stats['completed_games']}  |  "
                f"Best: {best_times}"
            )
        )

    def _add_row(self, parent, values, header: bool = False, success: Optional[bool] = None) -> None:
        palette = self.theme.palette
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)

        widths = [180, 90, 80, 70, 70, 80, 110]
        for value, width in zip(values, widths):
            color = palette.text
            if header:
                font = ctk.CTkFont(size=12, weight="bold")
                color = palette.text_muted
            else:
                font = ctk.CTkFont(size=12)
                if "Completed" in str(value):
                    color = palette.success
                elif "Incomplete" in str(value):
                    color = palette.warning
            ctk.CTkLabel(
                row, text=str(value), font=font, text_color=color, width=width, anchor="w"
            ).pack(side="left", padx=4)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_search(self) -> None:
        keyword = self.search_entry.get().strip() or None
        difficulty = self.difficulty_filter.get()
        completed_only = self.completed_only_var.get()
        games = self.database.search_games(
            difficulty=difficulty, completed_only=completed_only, keyword=keyword
        )
        self._populate(games)

    def _on_clear_filters(self) -> None:
        self.search_entry.delete(0, "end")
        self.difficulty_filter.set("All")
        self.completed_only_var.set(False)
        self._populate(self.database.fetch_all_games())

    def _on_clear_history(self) -> None:
        confirm = ctk.CTkInputDialog(
            text="Type DELETE to permanently clear all history.",
            title="Confirm Clear History",
        )
        response = confirm.get_input()
        if response == "DELETE":
            self.database.clear_history()
            self._populate([])
