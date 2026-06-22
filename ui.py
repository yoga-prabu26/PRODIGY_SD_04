"""
ui.py
------
The main application window and all UI composition for
SudokuMaster Pro. Built with CustomTkinter for a modern dark/light
themed desktop experience.

Architecture notes:
    - SudokuApp (a ctk.CTk) owns the entire game state and assembles
      the navbar, board, number pad, and right-hand information
      panels.
    - The board itself is rendered on a plain tkinter.Canvas (wrapped
      visually to match the CTk theme) because a canvas gives full
      control over grid-line thickness, cell highlighting, and text
      placement that a grid of buttons cannot easily achieve.
    - All game logic (solving, generating, validating) is delegated
      to the dedicated modules; ui.py focuses purely on presentation
      and event wiring.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from typing import Optional, Tuple, List

from sudoku_solver import SudokuSolver, Grid, GRID_SIZE, BOX_SIZE, EMPTY
from puzzle_generator import PuzzleGenerator, Difficulty
from validator import SudokuValidator
from database import Database, GameRecord
from theme_manager import ThemeManager
from save_manager import SaveManager
from history_manager import HistoryWindow

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900
CELL_SIZE = 74  # pixels; 9 * 74 = 666px board, sized to dominate the left panel
BOARD_PIXELS = CELL_SIZE * GRID_SIZE


class SudokuApp(ctk.CTk):
    """The root application window for SudokuMaster Pro."""

    def __init__(self) -> None:
        super().__init__()

        # --- Engines & persistence ----------------------------------
        self.theme = ThemeManager()
        self.database = Database()
        self.generator = PuzzleGenerator()
        self.solver = SudokuSolver()
        self.save_manager = SaveManager()

        # --- Game state -----------------------------------------------
        self.puzzle: Grid = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.solution: Grid = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.given_mask: List[List[bool]] = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.difficulty: Difficulty = Difficulty.MEDIUM
        self.selected_cell: Optional[Tuple[int, int]] = None
        self.error_cells: set = set()
        self.hinted_cells: set = set()

        self.moves: int = 0
        self.hints_used: int = 0
        self.mistakes: int = 0
        self.elapsed_seconds: int = 0
        self.timer_running: bool = False
        self.game_completed: bool = False
        self.auto_check_var = ctk.BooleanVar(value=False)

        # --- Window setup -----------------------------------------------
        self.title("SudokuMaster Pro")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(1280, 760)
        self.configure(fg_color=self.theme.palette.background)

        self.theme.subscribe(self._on_theme_changed)

        self._build_layout()
        self._bind_keyboard()

        # Kick off with a fresh Medium puzzle so the app looks alive
        # the moment it opens.
        self.new_game(Difficulty.MEDIUM)
        self._tick_timer()

    # ======================================================================
    # LAYOUT CONSTRUCTION
    # ======================================================================
    def _build_layout(self) -> None:
        self._build_navbar()

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=7)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        self.left_panel = ctk.CTkFrame(body, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        self.right_panel = ctk.CTkScrollableFrame(body, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew")

        self._build_board_area(self.left_panel)
        self._build_right_panel(self.right_panel)

    def _build_navbar(self) -> None:
        palette = self.theme.palette
        self.navbar = ctk.CTkFrame(self, fg_color=palette.card, height=70, corner_radius=0)
        self.navbar.pack(fill="x", side="top")

        left_section = ctk.CTkFrame(self.navbar, fg_color="transparent")
        left_section.pack(side="left", padx=24, pady=10)

        self.logo_label = ctk.CTkLabel(
            left_section,
            text="◆",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=palette.primary,
        )
        self.logo_label.pack(side="left", padx=(0, 10))

        title_block = ctk.CTkFrame(left_section, fg_color="transparent")
        title_block.pack(side="left")

        self.title_label = ctk.CTkLabel(
            title_block,
            text="SudokuMaster Pro",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.text,
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            title_block,
            text="Professional Puzzle Suite",
            font=ctk.CTkFont(size=11),
            text_color=palette.text_muted,
        )
        self.subtitle_label.pack(anchor="w")

        right_section = ctk.CTkFrame(self.navbar, fg_color="transparent")
        right_section.pack(side="right", padx=24, pady=14)

        self.theme_toggle_btn = ctk.CTkButton(
            right_section,
            text="☀ Light Mode",
            width=130,
            fg_color=palette.card_alt,
            hover_color=palette.border,
            text_color=palette.text,
            command=self.toggle_theme,
        )
        self.theme_toggle_btn.pack(side="right", padx=(8, 0))

        self.history_btn = ctk.CTkButton(
            right_section,
            text="🕘 History",
            width=120,
            fg_color=palette.card_alt,
            hover_color=palette.border,
            text_color=palette.text,
            command=self.show_history,
        )
        self.history_btn.pack(side="right", padx=(8, 0))

        self.new_game_btn = ctk.CTkButton(
            right_section,
            text="+ New Game",
            width=130,
            fg_color=palette.primary,
            hover_color=palette.primary_hover,
            command=lambda: self.new_game(self.difficulty),
        )
        self.new_game_btn.pack(side="right", padx=(8, 0))

    # ----------------------------------------------------------------
    # Board + number pad (left, ~70%)
    # ----------------------------------------------------------------
    def _build_board_area(self, parent) -> None:
        palette = self.theme.palette

        board_card = ctk.CTkFrame(parent, fg_color=palette.card, corner_radius=16)
        board_card.pack(fill="both", expand=True)

        board_wrapper = ctk.CTkFrame(board_card, fg_color="transparent")
        board_wrapper.pack(expand=True, pady=(20, 8))

        self.canvas = tk.Canvas(
            board_wrapper,
            width=BOARD_PIXELS,
            height=BOARD_PIXELS,
            bg=palette.board_bg,
            highlightthickness=0,
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # --- Number pad -------------------------------------------------
        numpad_frame = ctk.CTkFrame(board_card, fg_color="transparent")
        numpad_frame.pack(pady=(4, 18))

        self.numpad_buttons = []
        for digit in range(1, 10):
            btn = ctk.CTkButton(
                numpad_frame,
                text=str(digit),
                width=56,
                height=56,
                corner_radius=10,
                font=ctk.CTkFont(size=18, weight="bold"),
                fg_color=palette.card_alt,
                hover_color=palette.primary,
                text_color=palette.text,
                command=lambda d=digit: self.enter_value(d),
            )
            btn.grid(row=0, column=digit - 1, padx=4)
            self.numpad_buttons.append(btn)

        erase_btn = ctk.CTkButton(
            numpad_frame,
            text="⌫",
            width=56,
            height=56,
            corner_radius=10,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=palette.danger,
            hover_color="#B91C1C",
            command=self.clear_cell,
        )
        erase_btn.grid(row=0, column=9, padx=(16, 4))

        self.draw_board()

    # ----------------------------------------------------------------
    # Right panel: cards (30%)
    # ----------------------------------------------------------------
    def _build_right_panel(self, parent) -> None:
        self._build_difficulty_card(parent)
        self._build_controls_card(parent)
        self._build_save_export_card(parent)
        self._build_info_card(parent)

    def _card(self, parent, title: str) -> ctk.CTkFrame:
        palette = self.theme.palette
        card = ctk.CTkFrame(parent, fg_color=palette.card, corner_radius=14)
        card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=palette.text,
        ).pack(anchor="w", padx=18, pady=(16, 8))
        return card

    def _build_difficulty_card(self, parent) -> None:
        palette = self.theme.palette
        card = self._card(parent, "Difficulty")

        button_row = ctk.CTkFrame(card, fg_color="transparent")
        button_row.pack(fill="x", padx=18, pady=(0, 18))
        button_row.grid_columnconfigure((0, 1), weight=1)

        self.difficulty_buttons = {}
        difficulties = [
            (Difficulty.EASY, palette.success),
            (Difficulty.MEDIUM, palette.primary),
            (Difficulty.HARD, palette.warning),
            (Difficulty.EXPERT, palette.purple),
        ]
        for index, (difficulty, color) in enumerate(difficulties):
            row, col = divmod(index, 2)
            btn = ctk.CTkButton(
                button_row,
                text=difficulty.value,
                fg_color=palette.card_alt,
                hover_color=color,
                text_color=palette.text,
                border_width=2,
                border_color=color,
                command=lambda d=difficulty: self.new_game(d),
            )
            btn.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
            self.difficulty_buttons[difficulty] = (btn, color)

    def _build_controls_card(self, parent) -> None:
        palette = self.theme.palette
        card = self._card(parent, "Game Controls")

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(0, 8))
        body.grid_columnconfigure((0, 1), weight=1)

        controls = [
            ("Generate Puzzle", lambda: self.new_game(self.difficulty), palette.primary),
            ("Solve Puzzle", self.solve_puzzle, palette.purple),
            ("Hint", self.give_hint, palette.warning),
            ("Reset", self.reset_puzzle, palette.card_alt),
            ("Clear Board", self.clear_board, palette.card_alt),
        ]
        for index, (label, command, color) in enumerate(controls):
            row, col = divmod(index, 2)
            btn = ctk.CTkButton(
                body,
                text=label,
                fg_color=color,
                hover_color=palette.primary_hover if color == palette.primary else palette.border,
                text_color=palette.text,
                command=command,
            )
            btn.grid(row=row, column=col, padx=4, pady=4, sticky="ew")

        switch_row = ctk.CTkFrame(card, fg_color="transparent")
        switch_row.pack(fill="x", padx=18, pady=(8, 18))
        ctk.CTkSwitch(
            switch_row,
            text="Auto-Check Mode",
            variable=self.auto_check_var,
            onvalue=True,
            offvalue=False,
            command=self.draw_board,
            text_color=palette.text,
        ).pack(anchor="w")

    def _build_save_export_card(self, parent) -> None:
        palette = self.theme.palette
        card = self._card(parent, "Save & Export")

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(0, 18))
        body.grid_columnconfigure((0, 1), weight=1)

        actions = [
            ("Save Game", self.save_game),
            ("Load Game", self.load_game),
            ("Export Puzzle", self.export_puzzle),
        ]
        for index, (label, command) in enumerate(actions):
            row, col = divmod(index, 2)
            ctk.CTkButton(
                body,
                text=label,
                fg_color=palette.card_alt,
                hover_color=palette.border,
                text_color=palette.text,
                command=command,
            ).grid(row=row, column=col, padx=4, pady=4, sticky="ew")

    def _build_info_card(self, parent) -> None:
        palette = self.theme.palette
        card = self._card(parent, "Game Information")

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=18, pady=(0, 18))
        grid.grid_columnconfigure((0, 1), weight=1)

        self.timer_label = self._info_tile(grid, "Timer", "00:00", 0, 0)
        self.moves_label = self._info_tile(grid, "Moves", "0", 0, 1)
        self.completion_label = self._info_tile(grid, "Completion", "0%", 1, 0)
        self.difficulty_label = self._info_tile(grid, "Difficulty", self.difficulty.value, 1, 1)

    def _info_tile(self, parent, label_text: str, value_text: str, row: int, col: int):
        palette = self.theme.palette
        tile = ctk.CTkFrame(parent, fg_color=palette.card_alt, corner_radius=10)
        tile.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

        ctk.CTkLabel(
            tile, text=label_text, font=ctk.CTkFont(size=11), text_color=palette.text_muted
        ).pack(anchor="w", padx=12, pady=(10, 0))

        value_label = ctk.CTkLabel(
            tile,
            text=value_text,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.text,
        )
        value_label.pack(anchor="w", padx=12, pady=(0, 10))
        return value_label

    # ======================================================================
    # BOARD RENDERING
    # ======================================================================
    def draw_board(self) -> None:
        """Full redraw of the canvas based on current game state."""
        palette = self.theme.palette
        self.canvas.delete("all")
        self.canvas.configure(bg=palette.board_bg)

        peers = self._peer_cells(self.selected_cell) if self.selected_cell else set()

        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x0, y0 = col * CELL_SIZE, row * CELL_SIZE
                x1, y1 = x0 + CELL_SIZE, y0 + CELL_SIZE

                fill_color = palette.cell_bg
                if (row, col) in self.error_cells:
                    fill_color = palette.cell_error_bg
                elif self.selected_cell == (row, col):
                    fill_color = palette.cell_selected_bg
                elif (row, col) in peers:
                    fill_color = palette.cell_peer_bg
                elif self.given_mask[row][col]:
                    fill_color = palette.cell_given_bg

                self.canvas.create_rectangle(
                    x0, y0, x1, y1, fill=fill_color, outline=""
                )

                value = self.puzzle[row][col]
                if value != EMPTY:
                    is_given = self.given_mask[row][col]
                    is_hinted = (row, col) in self.hinted_cells
                    if self.selected_cell == (row, col):
                        text_color = palette.text
                    elif is_given:
                        text_color = palette.text
                    elif is_hinted:
                        text_color = palette.warning
                    elif (row, col) in self.error_cells:
                        text_color = palette.danger
                    else:
                        text_color = palette.primary
                    font_weight = "bold" if is_given else "normal"
                    self.canvas.create_text(
                        x0 + CELL_SIZE / 2,
                        y0 + CELL_SIZE / 2,
                        text=str(value),
                        fill=text_color,
                        font=("Segoe UI", 24, font_weight),
                    )

        # Thin grid lines.
        for index in range(GRID_SIZE + 1):
            width = 3 if index % BOX_SIZE == 0 else 1
            color = palette.grid_line_strong if index % BOX_SIZE == 0 else palette.grid_line
            self.canvas.create_line(0, index * CELL_SIZE, BOARD_PIXELS, index * CELL_SIZE, fill=color, width=width)
            self.canvas.create_line(index * CELL_SIZE, 0, index * CELL_SIZE, BOARD_PIXELS, fill=color, width=width)

    def _peer_cells(self, cell: Tuple[int, int]) -> set:
        row, col = cell
        peers = set()
        for c in range(GRID_SIZE):
            peers.add((row, c))
        for r in range(GRID_SIZE):
            peers.add((r, col))
        box_row, box_col = (row // BOX_SIZE) * BOX_SIZE, (col // BOX_SIZE) * BOX_SIZE
        for r in range(box_row, box_row + BOX_SIZE):
            for c in range(box_col, box_col + BOX_SIZE):
                peers.add((r, c))
        peers.discard(cell)
        return peers

    # ======================================================================
    # EVENT HANDLING
    # ======================================================================
    def _on_canvas_click(self, event) -> None:
        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            self.select_cell(row, col)

    def select_cell(self, row: int, col: int) -> None:
        self.selected_cell = (row, col)
        self.draw_board()

    def _bind_keyboard(self) -> None:
        for digit in range(1, 10):
            self.bind(str(digit), lambda event, d=digit: self.enter_value(d))
        self.bind("<BackSpace>", lambda event: self.clear_cell())
        self.bind("<Delete>", lambda event: self.clear_cell())
        self.bind("<Up>", lambda event: self._navigate(-1, 0))
        self.bind("<Down>", lambda event: self._navigate(1, 0))
        self.bind("<Left>", lambda event: self._navigate(0, -1))
        self.bind("<Right>", lambda event: self._navigate(0, 1))

    def _navigate(self, d_row: int, d_col: int) -> None:
        if self.selected_cell is None:
            self.select_cell(0, 0)
            return
        row, col = self.selected_cell
        new_row = max(0, min(GRID_SIZE - 1, row + d_row))
        new_col = max(0, min(GRID_SIZE - 1, col + d_col))
        self.select_cell(new_row, new_col)

    # ======================================================================
    # GAMEPLAY ACTIONS
    # ======================================================================
    def enter_value(self, value: int) -> None:
        if self.selected_cell is None or self.game_completed:
            return
        row, col = self.selected_cell
        if self.given_mask[row][col]:
            return  # Can't overwrite a given clue.

        self.puzzle[row][col] = value
        self.moves += 1
        self._refresh_error_state()
        self.draw_board()
        self._update_info_panel()
        self._check_win_condition()

    def clear_cell(self) -> None:
        if self.selected_cell is None or self.game_completed:
            return
        row, col = self.selected_cell
        if self.given_mask[row][col]:
            return
        if self.puzzle[row][col] != EMPTY:
            self.puzzle[row][col] = EMPTY
            self.moves += 1
        self.hinted_cells.discard((row, col))
        self._refresh_error_state()
        self.draw_board()
        self._update_info_panel()

    def _refresh_error_state(self) -> None:
        """
        Recompute which cells are in an error state. Rule violations
        (duplicate digit in row/col/box) are always flagged. If
        Auto-Check Mode is enabled, cells that don't match the known
        solution are also flagged, even without a duplicate.
        """
        self.error_cells = set()
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if self.puzzle[row][col] == EMPTY or self.given_mask[row][col]:
                    continue
                conflicts = SudokuValidator.find_conflicts(self.puzzle, row, col)
                if conflicts:
                    self.error_cells.add((row, col))
                    self.error_cells.update(conflicts)
                elif self.auto_check_var.get():
                    if self.puzzle[row][col] != self.solution[row][col]:
                        self.error_cells.add((row, col))

        self.mistakes = SudokuValidator.count_mistakes(self.puzzle, self.solution, self.given_mask)

    def give_hint(self) -> None:
        if self.game_completed:
            return
        empty_cells = [
            (r, c)
            for r in range(GRID_SIZE)
            for c in range(GRID_SIZE)
            if self.puzzle[r][c] == EMPTY
        ]
        if not empty_cells:
            messagebox.showinfo("Hint", "The board is already full!")
            return

        # Prefer the currently selected cell if it's empty; otherwise
        # pick the first empty cell found.
        target = self.selected_cell if self.selected_cell in empty_cells else empty_cells[0]
        row, col = target
        self.puzzle[row][col] = self.solution[row][col]
        self.hinted_cells.add((row, col))
        self.hints_used += 1
        self.moves += 1
        self.selected_cell = (row, col)
        self._refresh_error_state()
        self.draw_board()
        self._update_info_panel()
        self._check_win_condition()

    def solve_puzzle(self) -> None:
        if messagebox.askyesno(
            "Solve Puzzle", "This will reveal the full solution and end the current game. Continue?"
        ):
            self.puzzle = [row[:] for row in self.solution]
            self.error_cells = set()
            self.hinted_cells = set()
            self.draw_board()
            self._update_info_panel()
            self._finish_game(completed=True, solved_by_user=False)

    def reset_puzzle(self) -> None:
        """Restore the puzzle to its original given state and reset progress counters."""
        self.puzzle = [
            [self._original_puzzle[r][c] for c in range(GRID_SIZE)] for r in range(GRID_SIZE)
        ]
        self.moves = 0
        self.hints_used = 0
        self.mistakes = 0
        self.elapsed_seconds = 0
        self.error_cells = set()
        self.hinted_cells = set()
        self.game_completed = False
        self.timer_running = True
        self.draw_board()
        self._update_info_panel()

    def clear_board(self) -> None:
        """Clear all player-entered values but keep the timer and move count running."""
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if not self.given_mask[row][col]:
                    self.puzzle[row][col] = EMPTY
        self.error_cells = set()
        self.hinted_cells = set()
        self.draw_board()
        self._update_info_panel()

    def _check_win_condition(self) -> None:
        if SudokuValidator.is_board_complete(self.puzzle):
            if SudokuValidator.is_board_correct(self.puzzle, self.solution):
                self._finish_game(completed=True, solved_by_user=True)
            else:
                messagebox.showwarning(
                    "Almost there!", "The board is full but a few entries are incorrect."
                )

    def _finish_game(self, completed: bool, solved_by_user: bool) -> None:
        self.game_completed = True
        self.timer_running = False

        completion_percent = SudokuValidator.completion_percentage(self.puzzle, self.given_mask)
        record = GameRecord(
            id=None,
            difficulty=self.difficulty.value,
            duration_seconds=self.elapsed_seconds,
            moves=self.moves,
            hints_used=self.hints_used,
            mistakes=self.mistakes,
            completed=completed,
            completion_percent=completion_percent,
            played_at=Database.now_iso(),
        )
        self.database.record_game(record)

        if solved_by_user:
            self._play_completion_animation()
            messagebox.showinfo(
                "Puzzle Solved!",
                f"Congratulations! You solved the {self.difficulty.value} puzzle in "
                f"{self.elapsed_seconds // 60}m {self.elapsed_seconds % 60}s with "
                f"{self.moves} moves and {self.hints_used} hints.",
            )

    def _play_completion_animation(self) -> None:
        """A short flash animation across the board to celebrate completion."""
        palette = self.theme.palette
        flash_colors = [palette.success, palette.primary, palette.purple, palette.board_bg]

        def flash(step: int = 0) -> None:
            if step >= len(flash_colors) * 2:
                self.draw_board()
                return
            color = flash_colors[step % len(flash_colors)]
            self.canvas.configure(bg=color)
            self.after(120, lambda: flash(step + 1))

        flash()

    # ======================================================================
    # NEW GAME / DIFFICULTY
    # ======================================================================
    def new_game(self, difficulty: Difficulty) -> None:
        self.difficulty = difficulty
        puzzle, solution = self.generator.generate(difficulty)
        self.puzzle = puzzle
        self.solution = solution
        self._original_puzzle = [row[:] for row in puzzle]
        self.given_mask = PuzzleGenerator.grid_to_given_mask(puzzle)

        self.selected_cell = None
        self.error_cells = set()
        self.hinted_cells = set()
        self.moves = 0
        self.hints_used = 0
        self.mistakes = 0
        self.elapsed_seconds = 0
        self.game_completed = False
        self.timer_running = True

        self._highlight_active_difficulty()
        self.draw_board()
        self._update_info_panel()

    def _highlight_active_difficulty(self) -> None:
        palette = self.theme.palette
        for difficulty, (btn, color) in self.difficulty_buttons.items():
            if difficulty == self.difficulty:
                btn.configure(fg_color=color)
            else:
                btn.configure(fg_color=palette.card_alt)

    # ======================================================================
    # TIMER
    # ======================================================================
    def _tick_timer(self) -> None:
        if self.timer_running and not self.game_completed:
            self.elapsed_seconds += 1
            self._update_info_panel()
        self.after(1000, self._tick_timer)

    def _update_info_panel(self) -> None:
        minutes, seconds = divmod(self.elapsed_seconds, 60)
        self.timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")
        self.moves_label.configure(text=str(self.moves))
        completion = SudokuValidator.completion_percentage(self.puzzle, self.given_mask)
        self.completion_label.configure(text=f"{completion}%")
        self.difficulty_label.configure(text=self.difficulty.value)

    # ======================================================================
    # SAVE / LOAD / EXPORT
    # ======================================================================
    def save_game(self) -> None:
        try:
            path = self.save_manager.save_game(
                puzzle=self.puzzle,
                solution=self.solution,
                given_mask=self.given_mask,
                difficulty=self.difficulty.value,
                elapsed_seconds=self.elapsed_seconds,
                moves=self.moves,
                hints_used=self.hints_used,
            )
            messagebox.showinfo("Game Saved", f"Your game was saved to:\n{path}")
        except OSError as error:
            messagebox.showerror("Save Failed", f"Could not save the game:\n{error}")

    def load_game(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Load Sudoku Save",
            initialdir=self.save_manager.list_saves() and "saves" or ".",
            filetypes=[("SudokuMaster Pro Save", "*.json")],
        )
        if not file_path:
            return
        try:
            data = self.save_manager.load_game(file_path)
        except (OSError, ValueError) as error:
            messagebox.showerror("Load Failed", f"Could not load this save file:\n{error}")
            return

        self.puzzle = data["puzzle"]
        self.solution = data["solution"]
        self.given_mask = data["given_mask"]
        self._original_puzzle = [
            [self.puzzle[r][c] if self.given_mask[r][c] else EMPTY for c in range(GRID_SIZE)]
            for r in range(GRID_SIZE)
        ]
        try:
            self.difficulty = Difficulty(data.get("difficulty", "Medium"))
        except ValueError:
            self.difficulty = Difficulty.MEDIUM

        self.elapsed_seconds = data.get("elapsed_seconds", 0)
        self.moves = data.get("moves", 0)
        self.hints_used = data.get("hints_used", 0)
        self.selected_cell = None
        self.hinted_cells = set()
        self.game_completed = False
        self.timer_running = True

        self._refresh_error_state()
        self._highlight_active_difficulty()
        self.draw_board()
        self._update_info_panel()
        messagebox.showinfo("Game Loaded", "Your saved game has been restored.")

    def export_puzzle(self) -> None:
        file_format = "json"
        if messagebox.askyesno(
            "Export Format", "Export as plain text (.txt)? Choose 'No' for JSON."
        ):
            file_format = "txt"
        try:
            path = self.save_manager.export_puzzle(
                self._original_puzzle, self.difficulty.value, file_format
            )
            messagebox.showinfo("Puzzle Exported", f"Puzzle exported to:\n{path}")
        except OSError as error:
            messagebox.showerror("Export Failed", f"Could not export the puzzle:\n{error}")

    # ======================================================================
    # HISTORY & THEME
    # ======================================================================
    def show_history(self) -> None:
        HistoryWindow(self, self.database, self.theme)

    def toggle_theme(self) -> None:
        self.theme.toggle()

    def _on_theme_changed(self) -> None:
        """
        Rebuild theme-dependent widgets. CustomTkinter widgets don't
        automatically re-skin on palette change, so the simplest
        reliable approach is to tear down and rebuild the dynamic
        portions of the UI.
        """
        palette = self.theme.palette
        ctk.set_appearance_mode("dark" if self.theme.is_dark else "light")
        self.configure(fg_color=palette.background)

        for widget in self.winfo_children():
            widget.destroy()

        self._build_layout()
        self._highlight_active_difficulty()
        self.draw_board()
        self._update_info_panel()
        self.theme_toggle_btn.configure(
            text="☀ Light Mode" if self.theme.is_dark else "🌙 Dark Mode"
        )


def run_app() -> None:
    """Entry point used by main.py to launch the application."""
    app = SudokuApp()
    app.mainloop()
