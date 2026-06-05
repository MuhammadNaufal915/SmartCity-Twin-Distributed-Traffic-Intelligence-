"""
Log Panel for SmartCity Twin.
Provides an auto-scrolling, color-coded terminal view of system logs and alerts.
"""

from __future__ import annotations

import time
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QComboBox, QPushButton,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor


class LogPanel(QWidget):
    """
    Console log panel.
    Displays timestamped events from the central controller and junctions.
    """

    LEVEL_COLORS = {
        'INFO': '#ffffff',      # White
        'WARNING': '#ffb74d',   # Orange/Yellow
        'EMERGENCY': '#ef5350', # Red
        'CRITICAL': '#e53935',  # Dark Red
    }

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(150)

        # State
        self._last_timestamp: float = 0.0
        self._current_filter: str = "ALL"
        self._all_logs: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # Header bar
        header = QHBoxLayout()
        header.setContentsMargins(4, 0, 4, 0)

        title = QLabel("📜 SYSTEM EVENT LOG")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setStyleSheet("color: #78b8ff; background: transparent;")
        header.addWidget(title)
        header.addStretch()

        # Filter combo
        filter_label = QLabel("Filter:")
        filter_label.setFont(QFont("Segoe UI", 9))
        filter_label.setStyleSheet("color: #8888aa; background: transparent;")
        header.addWidget(filter_label)

        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["ALL", "INFO", "WARNING", "EMERGENCY"])
        self._filter_combo.setFont(QFont("Segoe UI", 9))
        self._filter_combo.setStyleSheet("""
            QComboBox {
                background-color: #1a1a2e;
                color: #ffffff;
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                padding: 2px 10px 2px 5px;
                min-width: 100px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a2e;
                color: #ffffff;
                selection-background-color: #2a2a4a;
            }
        """)
        self._filter_combo.currentTextChanged.connect(self._on_filter_changed)
        header.addWidget(self._filter_combo)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setFont(QFont("Segoe UI", 9))
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a4a;
                color: #ffffff;
                border: 1px solid #3a3a6a;
                border-radius: 4px;
                padding: 3px 10px;
            }
            QPushButton:hover {
                background-color: #3a3a6a;
            }
            QPushButton:pressed {
                background-color: #1a1a2e;
            }
        """)
        clear_btn.clicked.connect(self.clear_logs)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # Text Console
        self._console = QTextEdit()
        self._console.setReadOnly(True)
        self._console.setFont(QFont("Consolas", 10))
        self._console.document().setMaximumBlockCount(500)
        self._console.setStyleSheet("""
            QTextEdit {
                background-color: #0d0d1a;
                color: #ffffff;
                border: 1px solid #20203a;
                border-radius: 6px;
                padding: 5px;
            }
        """)
        layout.addWidget(self._console)

    def _on_filter_changed(self, text: str) -> None:
        """Handle filter selection change."""
        self._current_filter = text
        self._rebuild_console()

    def clear_logs(self) -> None:
        """Clear visible and stored logs."""
        self._console.clear()
        self._all_logs.clear()
        self._last_timestamp = 0.0

    def update_logs(self, log_entries: list[dict]) -> None:
        """
        Update the log display with new entries from the controller.
        
        Appends new logs or rebuilds if log size decreased (reset).
        """
        if not log_entries:
            if self._all_logs:
                # Logs were cleared in controller
                self.clear_logs()
            return

        # Check if logs were reset
        if len(log_entries) < len(self._all_logs) or (self._all_logs and log_entries[0]['timestamp'] > self._all_logs[-1]['timestamp']):
            self.clear_logs()

        self._all_logs = log_entries

        # Find new entries
        new_entries = [e for e in log_entries if e['timestamp'] > self._last_timestamp]
        if not new_entries:
            return

        # Update last timestamp
        self._last_timestamp = new_entries[-1]['timestamp']

        # Append new entries to console if they match filter
        for entry in new_entries:
            if self._matches_filter(entry):
                self._append_entry_to_console(entry)

    def _matches_filter(self, entry: dict) -> bool:
        """Check if log entry matches current level filter."""
        if self._current_filter == "ALL":
            return True
        return entry.get('level', 'INFO') == self._current_filter

    def _rebuild_console(self) -> None:
        """Clear and redraw console using all current logs matching filter."""
        self._console.clear()
        for entry in self._all_logs:
            if self._matches_filter(entry):
                self._append_entry_to_console(entry)

    def _append_entry_to_console(self, entry: dict) -> None:
        """Render a single log entry into QTextEdit as HTML."""
        timestamp_str = time.strftime("%H:%M:%S", time.localtime(entry.get('timestamp', time.time())))
        level = entry.get('level', 'INFO')
        message = entry.get('message', '')
        color = self.LEVEL_COLORS.get(level, '#ffffff')

        html = (
            f"<span style='color: #8888aa;'>[{timestamp_str}]</span> "
            f"<span style='color: {color}; font-weight: bold;'>[{level}]</span> "
            f"<span style='color: {color};'>{message}</span>"
        )
        self._console.append(html)

        # Move cursor to end to auto-scroll
        self._console.moveCursor(QTextCursor.MoveOperation.End)
