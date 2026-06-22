# SudokuMaster Pro

A professional, desktop Sudoku application built with **Python** and **CustomTkinter** — designed to look and feel like a real commercial puzzle product rather than a typical student assignment.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-3B82F6)
![SQLite](https://img.shields.io/badge/Database-SQLite-8B5CF6)
![License](https://img.shields.io/badge/License-MIT-22C55E)

---

## Overview

SudokuMaster Pro is a full-featured Sudoku desktop app where the **board is the centerpiece** of the experience — large, clean, and free of visual clutter. It pairs a from-scratch **backtracking + MRV heuristic solver** with a **uniqueness-guaranteed puzzle generator**, persistent **SQLite-backed statistics and history**, and a polished dark/light themed interface.

This project was built as a standalone application — independent of any prior Sudoku implementation — with an emphasis on clean modular architecture suitable for technical review.

## Screenshots

> Add your own screenshots to the `screenshots/` folder and reference them here, e.g.:
> `![Dark Mode](screenshots/dark_mode.png)`

## Key Features

### Core Gameplay
- ✅ Procedural puzzle generation across **4 difficulty levels** (Easy, Medium, Hard, Expert)
- ✅ Backtracking solver enhanced with the **Minimum Remaining Values (MRV)** heuristic
- ✅ Guaranteed **unique-solution** puzzles via solution-counting during generation
- ✅ One-click **full solve**, **hint system**, **reset**, and **clear board**
- ✅ **Keyboard input** (digits 1–9, Backspace/Delete) and on-screen **number pad**
- ✅ **Arrow-key navigation** across the grid
- ✅ Real-time **row / column / box highlighting** for the selected cell
- ✅ **Invalid entry highlighting** (rule-violation detection)
- ✅ Optional **Auto-Check Mode** for instant mistake detection against the solution

### Productivity & Persistence
- ✅ **Save Game** / **Load Game** (full state, JSON-backed, resumable)
- ✅ **Export Puzzle** (JSON or plain text, shareable without revealing the solution)
- ✅ **Game Timer**, **Move Counter**, and live **Completion %**
- ✅ **SQLite-backed** statistics: total games, completions, best times per difficulty
- ✅ Searchable **History window** with filters (difficulty, completion status, keyword)
- ✅ **Completion animation** on a successfully solved board

### Design
- ✅ Dark / Light **theme toggle**
- ✅ Board occupies ~70% of the window — the puzzle stays the visual focus
- ✅ Commercial-grade color system (primary, success, warning, purple accents)
- ✅ Fully responsive card-based right-hand control panel

## Tech Stack

| Layer            | Technology                          |
|------------------|--------------------------------------|
| UI Framework     | CustomTkinter (built on Tkinter)     |
| Language         | Python 3.11+                         |
| Persistence      | SQLite3 (history/stats), JSON (saves/exports) |
| Architecture     | Modular, Object-Oriented             |

## Project Structure

```
SudokuMasterPro/
│
├── main.py                # Application entry point
├── ui.py                  # Main window, layout, and all UI event handling
├── sudoku_solver.py        # Backtracking + MRV solving engine
├── puzzle_generator.py     # Puzzle generation with uniqueness guarantee
├── validator.py             # Move validation, mistake & completion logic
├── database.py              # SQLite persistence for history & statistics
├── history_manager.py       # Searchable history window (Toplevel UI)
├── theme_manager.py          # Dark/Light palette definitions & switching
├── save_manager.py           # Save / Load / Export (JSON file I/O)
│
├── assets/                 # Icons / static assets
├── screenshots/            # App screenshots for documentation
├── exports/                 # Exported puzzles land here
├── saves/                    # Saved games land here
│
├── README.md
├── LICENSE
└── requirements.txt
```

## Architecture Highlights

- **Separation of concerns**: solving, generating, validating, persisting, theming, and rendering each live in their own module. `ui.py` never contains raw Sudoku logic, and the engine modules never import Tkinter.
- **MRV Backtracking Solver**: rather than scanning cells left-to-right, the solver always branches on the empty cell with the *fewest* legal candidates first, pruning the search tree dramatically — Expert puzzles still generate in well under a second.
- **Uniqueness-guaranteed generation**: the generator "digs holes" into a fully solved grid one cell at a time, using `count_solutions(limit=2)` after each removal to confirm the puzzle still has exactly one valid solution before committing to it.
- **Stateless validators**: `SudokuValidator` is a collection of static methods operating purely on grid data, making it trivial to unit test independent of any UI.

## Getting Started

### Prerequisites
- Python 3.11 or newer
- pip

### Installation

```bash
git clone https://github.com/<your-username>/SudokuMasterPro.git
cd SudokuMasterPro
pip install -r requirements.txt
```

### Run the App

```bash
python main.py
```

## Controls

| Action                 | Input                              |
|------------------------|--------------------------------------|
| Select a cell           | Click on the board                  |
| Enter a digit            | Number keys `1-9` or the number pad |
| Clear a cell              | `Backspace` / `Delete` or the ⌫ button |
| Move selection             | Arrow keys                         |
| New puzzle                   | "+ New Game" or a difficulty card button |
| Get a hint                    | "Hint" button                      |
| Reveal solution                 | "Solve Puzzle" button             |

## Roadmap Ideas

- [ ] Pencil-mark / candidate-notes mode
- [ ] Daily challenge puzzle with shared seed
- [ ] Leaderboard sync across devices
- [ ] Custom puzzle import (paste a grid)

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Author

Built by **Yoga Prabu** as a portfolio-grade desktop application project.
