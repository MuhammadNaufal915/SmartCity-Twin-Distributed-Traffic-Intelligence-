"""
Monitoring Panel for SmartCity Twin.
Real-time node status cards showing each junction's
MCU state including vehicle count, density, light state, etc.
"""

from __future__ import annotations

import math
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush

from communication.queues import NODE_IDS


class StatusIndicator(QWidget):
    """Small colored circle indicator."""

    def __init__(self, size: int = 12, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._color = QColor(100, 100, 100)
        self._size = size
        self.setFixedSize(size + 4, size + 4)

    def set_color(self, color: QColor) -> None:
        self._color = color
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self._color))
        painter.drawEllipse(2, 2, self._size, self._size)


class NodeCard(QFrame):
    """
    Status card for a single junction node.
    
    Displays:
    - Node name and activity indicator
    - Vehicle count
    - Traffic density level
    - Current light state
    - Green duration
    - Congestion status
    - Emergency status
    - Message count
    """

    DISPLAY_NAMES = {
        'junction_a': 'JUNCTION A',
        'junction_b': 'JUNCTION B',
        'junction_c': 'JUNCTION C',
        'junction_d': 'JUNCTION D',
    }

    def __init__(self, node_id: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.node_id = node_id
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            NodeCard {
                background-color: #1a1a2e;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 8, 10, 8)

        # Header
        header = QHBoxLayout()
        self._status_indicator = StatusIndicator(10)
        self._status_indicator.set_color(QColor(100, 100, 100))
        header.addWidget(self._status_indicator)

        name_label = QLabel(self.DISPLAY_NAMES.get(node_id, node_id))
        name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #78b8ff; background: transparent; border: none;")
        header.addWidget(name_label)
        header.addStretch()
        layout.addLayout(header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #2a2a4a; max-height: 1px; border: none;")
        layout.addWidget(sep)

        # Status fields
        self._fields: dict[str, QLabel] = {}
        field_defs = [
            ('vehicles', '🚗 Vehicles', '0'),
            ('density', '📊 Density', 'LOW'),
            ('light', '🚦 Light', 'RED'),
            ('green_time', '⏱️ Green Time', '10s'),
            ('congestion', '⚠️ Congestion', 'No'),
            ('emergency', '🚨 Emergency', 'No'),
            ('messages', '📨 Messages', '0'),
            ('status', '⚡ Status', 'Offline'),
        ]

        grid = QGridLayout()
        grid.setSpacing(3)
        for i, (key, label_text, default) in enumerate(field_defs):
            label = QLabel(label_text)
            label.setFont(QFont("Segoe UI", 9))
            label.setStyleSheet("color: #8888aa; background: transparent; border: none;")

            value = QLabel(default)
            value.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            value.setStyleSheet("color: #ffffff; background: transparent; border: none;")
            value.setAlignment(Qt.AlignmentFlag.AlignRight)

            grid.addWidget(label, i, 0)
            grid.addWidget(value, i, 1)
            self._fields[key] = value

        layout.addLayout(grid)

    def update_status(
        self,
        vehicle_count: int,
        density_level: str,
        light_state: str,
        green_duration: int,
        congestion: bool,
        emergency: bool,
        message_count: int,
        is_active: bool,
    ) -> None:
        """Update all fields with latest node status."""
        # Activity indicator
        if is_active:
            self._status_indicator.set_color(QColor(76, 175, 80))
        else:
            self._status_indicator.set_color(QColor(100, 100, 100))

        # Vehicle count
        self._fields['vehicles'].setText(str(vehicle_count))
        if vehicle_count > 40:
            self._fields['vehicles'].setStyleSheet(
                "color: #f44336; font-weight: bold; background: transparent; border: none;"
            )
        elif vehicle_count > 20:
            self._fields['vehicles'].setStyleSheet(
                "color: #ff9800; font-weight: bold; background: transparent; border: none;"
            )
        else:
            self._fields['vehicles'].setStyleSheet(
                "color: #4caf50; font-weight: bold; background: transparent; border: none;"
            )

        # Density
        density_colors = {
            'LOW': '#4caf50',
            'MEDIUM': '#ffc107',
            'HIGH': '#ff9800',
            'CRITICAL': '#f44336',
        }
        d_color = density_colors.get(density_level, '#ffffff')
        self._fields['density'].setText(density_level)
        self._fields['density'].setStyleSheet(
            f"color: {d_color}; font-weight: bold; background: transparent; border: none;"
        )

        # Light state
        light_colors = {
            'GREEN': '#4caf50',
            'YELLOW': '#ffc107',
            'RED': '#f44336',
        }
        l_color = light_colors.get(light_state, '#ffffff')
        self._fields['light'].setText(light_state)
        self._fields['light'].setStyleSheet(
            f"color: {l_color}; font-weight: bold; background: transparent; border: none;"
        )

        # Green time
        self._fields['green_time'].setText(f"{green_duration}s")
        self._fields['green_time'].setStyleSheet(
            "color: #4fc3f7; font-weight: bold; background: transparent; border: none;"
        )

        # Congestion
        if congestion:
            self._fields['congestion'].setText("⚠ YES")
            self._fields['congestion'].setStyleSheet(
                "color: #ff5722; font-weight: bold; background: transparent; border: none;"
            )
        else:
            self._fields['congestion'].setText("No")
            self._fields['congestion'].setStyleSheet(
                "color: #66bb6a; font-weight: bold; background: transparent; border: none;"
            )

        # Emergency
        if emergency:
            self._fields['emergency'].setText("🚨 ACTIVE")
            self._fields['emergency'].setStyleSheet(
                "color: #f44336; font-weight: bold; background: transparent; border: none;"
            )
        else:
            self._fields['emergency'].setText("No")
            self._fields['emergency'].setStyleSheet(
                "color: #66bb6a; font-weight: bold; background: transparent; border: none;"
            )

        # Messages
        self._fields['messages'].setText(str(message_count))
        self._fields['messages'].setStyleSheet(
            "color: #ce93d8; font-weight: bold; background: transparent; border: none;"
        )

        # Processing status
        status_text = "● Online" if is_active else "○ Offline"
        status_color = "#4caf50" if is_active else "#666666"
        self._fields['status'].setText(status_text)
        self._fields['status'].setStyleSheet(
            f"color: {status_color}; font-weight: bold; background: transparent; border: none;"
        )


class MonitoringPanel(QWidget):
    """
    Real-time node monitoring panel.
    Shows status cards for all 4 junction nodes.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(4, 4, 4, 4)

        # Title
        title = QLabel("📡 NODE MONITORING")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #78b8ff; padding: 4px; background: transparent;")
        layout.addWidget(title)

        # Node cards
        self._cards: dict[str, NodeCard] = {}
        for node_id in NODE_IDS:
            card = NodeCard(node_id)
            self._cards[node_id] = card
            layout.addWidget(card)

        layout.addStretch()

    def update_node(
        self,
        node_id: str,
        vehicle_count: int,
        density_level: str,
        light_state: str,
        green_duration: int,
        congestion: bool,
        emergency: bool,
        message_count: int,
        is_active: bool,
    ) -> None:
        """Update a specific node's status card."""
        if node_id in self._cards:
            self._cards[node_id].update_status(
                vehicle_count, density_level, light_state,
                green_duration, congestion, emergency,
                message_count, is_active,
            )
