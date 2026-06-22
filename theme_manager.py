"""
theme_manager.py
-----------------
Centralizes all color/style values for SudokuMaster Pro and exposes a
single ThemeManager that the UI queries instead of hardcoding colors
throughout the codebase. Supports Dark (default) and Light themes.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    """Immutable bundle of colors that define one visual theme."""
    background: str
    card: str
    card_alt: str
    primary: str
    primary_hover: str
    success: str
    warning: str
    danger: str
    purple: str
    text: str
    text_muted: str
    border: str
    board_bg: str
    cell_bg: str
    cell_given_bg: str
    cell_selected_bg: str
    cell_peer_bg: str
    cell_error_bg: str
    grid_line: str
    grid_line_strong: str


DARK_PALETTE = Palette(
    background="#0B1220",
    card="#111827",
    card_alt="#1A2333",
    primary="#3B82F6",
    primary_hover="#2563EB",
    success="#22C55E",
    warning="#F59E0B",
    danger="#EF4444",
    purple="#8B5CF6",
    text="#F9FAFB",
    text_muted="#9CA3AF",
    border="#1F2937",
    board_bg="#0F172A",
    cell_bg="#172033",
    cell_given_bg="#1C2740",
    cell_selected_bg="#2563EB",
    cell_peer_bg="#1E3A5F",
    cell_error_bg="#4C1D1D",
    grid_line="#2A3650",
    grid_line_strong="#3B82F6",
)

LIGHT_PALETTE = Palette(
    background="#F3F4F6",
    card="#FFFFFF",
    card_alt="#F9FAFB",
    primary="#3B82F6",
    primary_hover="#2563EB",
    success="#16A34A",
    warning="#D97706",
    danger="#DC2626",
    purple="#7C3AED",
    text="#111827",
    text_muted="#6B7280",
    border="#E5E7EB",
    board_bg="#FFFFFF",
    cell_bg="#F3F4F6",
    cell_given_bg="#E5E7EB",
    cell_selected_bg="#93C5FD",
    cell_peer_bg="#DBEAFE",
    cell_error_bg="#FECACA",
    grid_line="#D1D5DB",
    grid_line_strong="#3B82F6",
)


class ThemeManager:
    """
    Holds the currently active palette and notifies subscribed
    callbacks whenever the theme is toggled, so widgets can restyle
    themselves without the app needing a full rebuild.
    """

    def __init__(self) -> None:
        self._is_dark = True
        self._subscribers = []

    @property
    def palette(self) -> Palette:
        return DARK_PALETTE if self._is_dark else LIGHT_PALETTE

    @property
    def is_dark(self) -> bool:
        return self._is_dark

    @property
    def mode_name(self) -> str:
        return "Dark" if self._is_dark else "Light"

    def toggle(self) -> None:
        self._is_dark = not self._is_dark
        self._notify()

    def subscribe(self, callback) -> None:
        """Register a no-arg callback invoked whenever the theme changes."""
        self._subscribers.append(callback)

    def _notify(self) -> None:
        for callback in self._subscribers:
            callback()
