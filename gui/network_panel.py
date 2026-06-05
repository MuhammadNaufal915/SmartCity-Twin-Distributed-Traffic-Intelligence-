"""
Network Panel for SmartCity Twin.
Displays the distributed network topology showing
node connectivity, central controller, and message flow.
"""

from __future__ import annotations

import math
import time
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont,
    QRadialGradient, QLinearGradient, QPainterPath,
)

from communication.queues import NODE_IDS, NEIGHBOR_MAP


class NetworkPanel(QWidget):
    """
    Distributed network topology visualization.
    
    Displays:
    - Central Controller node
    - 4 Junction nodes
    - Node-to-node connections (based on neighbor map)
    - Node-to-controller connections
    - Animated message flow particles
    """

    # Node positions (relative to widget center)
    NODE_LAYOUT = {
        'controller': (0, 0),
        'junction_a': (-120, -100),
        'junction_b': (120, -100),
        'junction_c': (-120, 100),
        'junction_d': (120, 100),
    }

    NODE_COLORS = {
        'controller': QColor(255, 193, 7),
        'junction_a': QColor(79, 195, 247),
        'junction_b': QColor(129, 199, 132),
        'junction_c': QColor(186, 104, 200),
        'junction_d': QColor(255, 138, 101),
    }

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(300, 280)

        self._phase: float = 0.0
        self._message_particles: list[dict] = []
        self._node_active: dict[str, bool] = {nid: False for nid in NODE_IDS}
        self._node_active['controller'] = False

        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)

    def set_node_active(self, node_id: str, active: bool) -> None:
        """Set whether a node is active."""
        self._node_active[node_id] = active
        self.update()

    def add_message_particle(self, source: str, target: str) -> None:
        """Add a visual message particle between two nodes."""
        if len(self._message_particles) < 20:
            self._message_particles.append({
                'source': source,
                'target': target,
                'progress': 0.0,
                'speed': 0.03,
            })

    def _animate(self) -> None:
        """Advance animation state."""
        self._phase += 0.05
        if self._phase > 2 * math.pi:
            self._phase -= 2 * math.pi

        # Move particles
        alive = []
        for p in self._message_particles:
            p['progress'] += p['speed']
            if p['progress'] < 1.0:
                alive.append(p)
        self._message_particles = alive

        # Spawn random particles when active
        if any(self._node_active.values()) and len(self._message_particles) < 8:
            import random
            active_nodes = [n for n, a in self._node_active.items() if a]
            if len(active_nodes) >= 2:
                src = random.choice(active_nodes)
                tgt = random.choice([n for n in active_nodes if n != src])
                self.add_message_particle(src, tgt)

        self.update()

    def _get_node_pos(self, node_id: str) -> QPointF:
        """Get absolute position for a node."""
        cx = self.width() / 2
        cy = self.height() / 2
        rx, ry = self.NODE_LAYOUT.get(node_id, (0, 0))
        # Scale based on widget size
        scale = min(self.width(), self.height()) / 350
        return QPointF(cx + rx * scale, cy + ry * scale)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(18, 18, 24))

        # Title
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.setPen(QPen(QColor(120, 180, 255, 180)))
        painter.drawText(QRectF(0, 5, self.width(), 25),
                        Qt.AlignmentFlag.AlignCenter, "🌐 DISTRIBUTED NETWORK")

        # Draw connections
        self._draw_connections(painter)

        # Draw message particles
        self._draw_particles(painter)

        # Draw nodes
        self._draw_nodes(painter)

        painter.end()

    def _draw_connections(self, painter: QPainter) -> None:
        """Draw connection lines between nodes."""
        # Controller to all nodes
        ctrl_pos = self._get_node_pos('controller')
        for node_id in NODE_IDS:
            node_pos = self._get_node_pos(node_id)
            active = self._node_active.get(node_id, False)
            color = QColor(100, 180, 255, 120) if active else QColor(60, 60, 80, 80)
            pen = QPen(color, 2, Qt.PenStyle.DashLine if not active else Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawLine(ctrl_pos, node_pos)

        # Node-to-node connections
        for node_id, neighbors in NEIGHBOR_MAP.items():
            node_pos = self._get_node_pos(node_id)
            for neighbor_id in neighbors:
                neighbor_pos = self._get_node_pos(neighbor_id)
                both_active = (
                    self._node_active.get(node_id, False)
                    and self._node_active.get(neighbor_id, False)
                )
                color = QColor(150, 255, 150, 100) if both_active else QColor(50, 80, 50, 50)
                pen = QPen(color, 1.5)
                painter.setPen(pen)
                painter.drawLine(node_pos, neighbor_pos)

    def _draw_particles(self, painter: QPainter) -> None:
        """Draw message flow particles."""
        for p in self._message_particles:
            src = self._get_node_pos(p['source'])
            tgt = self._get_node_pos(p['target'])
            t = p['progress']

            x = src.x() + (tgt.x() - src.x()) * t
            y = src.y() + (tgt.y() - src.y()) * t

            # Glowing particle
            alpha = int(200 * (1.0 - abs(t - 0.5) * 2))
            particle_color = QColor(100, 200, 255, max(alpha, 50))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(particle_color))
            painter.drawEllipse(QPointF(x, y), 4, 4)

    def _draw_nodes(self, painter: QPainter) -> None:
        """Draw node circles with labels."""
        for node_id in ['controller'] + list(NODE_IDS):
            pos = self._get_node_pos(node_id)
            color = self.NODE_COLORS.get(node_id, QColor(150, 150, 150))
            active = self._node_active.get(node_id, False)
            radius = 22 if node_id == 'controller' else 18

            # Glow effect for active nodes
            if active:
                glow = QRadialGradient(pos, radius + 12)
                glow.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 60))
                glow.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(glow))
                painter.drawEllipse(pos, radius + 12, radius + 12)

            # Node circle
            gradient = QRadialGradient(pos, radius)
            if active:
                gradient.setColorAt(0, color.lighter(140))
                gradient.setColorAt(1, color)
            else:
                gradient.setColorAt(0, QColor(80, 80, 80))
                gradient.setColorAt(1, QColor(50, 50, 50))

            painter.setPen(QPen(QColor(200, 200, 200, 100), 1.5))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(pos, radius, radius)

            # Label
            label = "CTRL" if node_id == 'controller' else node_id[-1].upper()
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(
                QRectF(pos.x() - 15, pos.y() - 10, 30, 20),
                Qt.AlignmentFlag.AlignCenter,
                label,
            )

            # Status label below
            status = "Online" if active else "Offline"
            painter.setFont(QFont("Segoe UI", 7))
            painter.setPen(QPen(QColor(150, 150, 150)))
            painter.drawText(
                QRectF(pos.x() - 25, pos.y() + radius + 2, 50, 15),
                Qt.AlignmentFlag.AlignCenter,
                status,
            )
