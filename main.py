"""
main.py
--------
Entry point for SudokuMaster Pro.

Run with:
    python main.py

Responsibilities:
    - Ensure required runtime folders exist (saves/, exports/).
    - Launch the CustomTkinter application defined in ui.py.
    - Provide a top-level error guard so unexpected exceptions don't
      crash silently with no useful message for the user.
"""

import os
import sys
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIRED_DIRS = ["saves", "exports", "assets", "screenshots"]


def ensure_runtime_directories() -> None:
    """Create any runtime folders the app expects, if they don't already exist."""
    for folder_name in REQUIRED_DIRS:
        folder_path = os.path.join(BASE_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)


def main() -> None:
    ensure_runtime_directories()

    try:
        from ui import run_app
        run_app()
    except ImportError as error:
        print("=" * 60)
        print("SudokuMaster Pro failed to start: a required dependency")
        print("appears to be missing.")
        print(f"Details: {error}")
        print("\nTry installing dependencies with:")
        print("    pip install -r requirements.txt")
        print("=" * 60)
        sys.exit(1)
    except Exception:
        print("=" * 60)
        print("SudokuMaster Pro encountered an unexpected error:")
        traceback.print_exc()
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
