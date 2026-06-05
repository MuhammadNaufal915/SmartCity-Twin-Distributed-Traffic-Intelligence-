"""
City Map widget for SmartCity Twin.
Animated digital twin city map showing intersections,
roads, traffic lights, and moving vehicles using QGraphicsView.
"""

from __future__ import annotations

import math
import random
import time
from typing import Optional

from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsEllipseItem, QGraphicsRectItem,
    QGraphicsLineItem, QGraphicsTextItem,
    QGraphicsDropShadowEffect, QWidget, QVBoxLayout, QLabel,
)
from PyQt6.QtCore import (
    Qt, QRectF, QPointF, QTimer, QPropertyAnimation,
    QEasingCurve, pyqtProperty, QObject,
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QRadialGradient,
    QLinearGradient, QPainterPath, QTransform,
)


# ─── Junction Positions ────────────────────────────────────────────
JUNCTION_POSITIONS = {
    'junction_a': QPointF(200, 150),   # Top-Left
    'junction_b': QPointF(600, 150),   # Top-Right
    'junction_c': QPointF(200, 450),   # Bottom-Left
    'junction_d': QPointF(600, 450),   # Bottom-Right
}

JUNCTION_LABELS = {
    'junction_a': 'A',
    'junction_b': 'B',
    'junction_c': 'C',
    'junction_d': 'D',
}

# Road connections (pairs of junctions)
ROAD_CONNECTIONS = [
    ('junction_a', 'junction_b'),  # Top horizontal
    ('junction_a', 'junction_c'),  # Left vertical
    ('junction_b', 'junction_d'),  # Right vertical
    ('junction_c', 'junction_d'),  # Bottom horizontal
]


# ─── Traffic Light Colors ──────────────────────────────────────────
LIGHT_COLORS = {
    'GREEN': QColor(76, 175, 80),
    'YELLOW': QColor(255, 193, 7),
    'RED': QColor(244, 67, 54),
}


class TrafficLightItem(QGraphicsItem):
    """Animated traffic light indicator at an intersection."""

    def __init__(self, parent: Optional[QGraphicsItem] = None) -> None:
        super().__init__(parent)
        self._state: str = "RED"
        self._glow_opacity: float = 0.8

    def set_state(self, state: str) -> None:
        """Set traffic light state (GREEN, YELLOW, RED)."""
        self._state = state
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(-15, -45, 30, 90)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Traffic light housing
        housing = QRectF(-12, -42, 24, 84)
        painter.setPen(QPen(QColor(40, 40, 40), 2))
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.drawRoundedRect(housing, 5, 5)

        # Three lights
        lights = [
            (QPointF(0, -26), "RED"),
            (QPointF(0, 0), "YELLOW"),
            (QPointF(0, 26), "GREEN"),
        ]

        for pos, color_name in lights:
            base_color = LIGHT_COLORS[color_name]
            if self._state == color_name:
                # Active light — bright with glow
                glow = QRadialGradient(pos, 14)
                glow.setColorAt(0, base_color.lighter(150))
                glow.setColorAt(0.5, base_color)
                glow.setColorAt(1, base_color.darker(200))
                painter.setBrush(QBrush(glow))
                painter.setPen(QPen(base_color.lighter(120), 1))
            else:
                # Inactive light — dim
                dim = QColor(base_color)
                dim.setAlpha(40)
                painter.setBrush(QBrush(dim))
                painter.setPen(QPen(QColor(60, 60, 60), 1))

            painter.drawEllipse(pos, 9, 9)


class IntersectionItem(QGraphicsItem):
    """
    Visual representation of a traffic junction/intersection.
    Includes the junction circle, label, traffic light, and status indicators.
    """

    RADIUS = 35

    def __init__(
        self,
        junction_id: str,
        position: QPointF,
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        super().__init__(parent)
        self.junction_id = junction_id
        self.label = JUNCTION_LABELS.get(junction_id, '?')
        self.setPos(position)

        # State
        self._density_level: str = "LOW"
        self._congestion: bool = False
        self._emergency: bool = False
        self._vehicle_count: int = 0
        self._light_state: str = "RED"
        self._pulse_phase: float = 0.0

        # Traffic light
        self._traffic_light = TrafficLightItem(self)
        self._traffic_light.setPos(50, -10)

    def update_status(
        self,
        vehicle_count: int,
        density_level: str,
        light_state: str,
        congestion: bool,
        emergency: bool,
    ) -> None:
        """Update intersection visual state."""
        self._vehicle_count = vehicle_count
        self._density_level = density_level
        self._light_state = light_state
        self._congestion = congestion
        self._emergency = emergency
        self._traffic_light.set_state(light_state)
        self.update()

    def advance_animation(self) -> None:
        """Advance animation state."""
        self._pulse_phase += 0.1
        if self._pulse_phase > 2 * math.pi:
            self._pulse_phase -= 2 * math.pi
        self.update()

    def boundingRect(self) -> QRectF:
        r = self.RADIUS + 20
        return QRectF(-r, -r, r * 2 + 80, r * 2 + 20)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.RADIUS

        # Congestion/Emergency glow effect
        if self._emergency:
            pulse = abs(math.sin(self._pulse_phase * 2))
            glow_color = QColor(244, 67, 54, int(100 * pulse))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow_color))
            painter.drawEllipse(QPointF(0, 0), r + 15, r + 15)
        elif self._congestion:
            pulse = abs(math.sin(self._pulse_phase))
            glow_color = QColor(255, 152, 0, int(80 * pulse))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow_color))
            painter.drawEllipse(QPointF(0, 0), r + 12, r + 12)

        # Junction circle with gradient
        density_colors = {
            'LOW': (QColor(76, 175, 80), QColor(56, 142, 60)),
            'MEDIUM': (QColor(255, 193, 7), QColor(245, 170, 0)),
            'HIGH': (QColor(255, 152, 0), QColor(230, 126, 0)),
            'CRITICAL': (QColor(244, 67, 54), QColor(211, 47, 47)),
        }
        c1, c2 = density_colors.get(
            self._density_level,
            (QColor(100, 100, 100), QColor(80, 80, 80))
        )

        gradient = QRadialGradient(QPointF(0, -5), r)
        gradient.setColorAt(0, c1.lighter(130))
        gradient.setColorAt(1, c2)

        painter.setPen(QPen(QColor(200, 200, 200, 150), 2))
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(0, 0), r, r)

        # Junction label
        font = QFont("Segoe UI", 18, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(QRectF(-r, -r, r * 2, r * 2), Qt.AlignmentFlag.AlignCenter, self.label)

        # Vehicle count badge
        badge_rect = QRectF(-18, r + 5, 36, 20)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(30, 30, 30, 200)))
        painter.drawRoundedRect(badge_rect, 8, 8)

        font_small = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font_small)
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, str(self._vehicle_count))


class VehicleItem(QGraphicsItem):
    """
    Visual representation of a vehicle moving along a road.
    Small colored rectangle that moves smoothly between intersections.
    """

    def __init__(
        self,
        start: QPointF,
        end: QPointF,
        color: QColor,
        is_emergency: bool = False,
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        super().__init__(parent)
        self._start = start
        self._end = end
        self._color = color
        self._is_emergency = is_emergency
        self._progress: float = 0.0
        self._speed: float = random.uniform(0.003, 0.012)
        self._alive: bool = True
        self._pulse: float = 0.0

        # Set initial position
        self.setPos(start)

    @property
    def is_alive(self) -> bool:
        return self._alive

    def advance_position(self) -> None:
        """Move the vehicle along its path."""
        if not self._alive:
            return

        self._progress += self._speed
        self._pulse += 0.15

        if self._progress >= 1.0:
            self._alive = False
            return

        # Interpolate position
        x = self._start.x() + (self._end.x() - self._start.x()) * self._progress
        y = self._start.y() + (self._end.y() - self._start.y()) * self._progress

        # Add slight lane offset
        dx = self._end.x() - self._start.x()
        dy = self._end.y() - self._start.y()
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
            # Perpendicular offset for lane
            nx = -dy / length * 8
            ny = dx / length * 8
            x += nx
            y += ny

        self.setPos(x, y)
        self.update()

    def boundingRect(self) -> QRectF:
        if self._is_emergency:
            return QRectF(-8, -5, 16, 10)
        return QRectF(-5, -4, 10, 8)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._is_emergency:
            # Emergency vehicle — larger with flashing effect
            pulse = abs(math.sin(self._pulse))
            glow = QColor(255, 0, 0, int(120 * pulse))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(QPointF(0, 0), 10, 10)

            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setBrush(QBrush(self._color))
            painter.drawRoundedRect(QRectF(-7, -4, 14, 8), 2, 2)
        else:
            # Regular vehicle
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self._color))
            painter.drawRoundedRect(QRectF(-4, -3, 8, 6), 2, 2)


class RoadItem(QGraphicsItem):
    """Visual representation of a road connecting two intersections."""

    def __init__(
        self,
        start: QPointF,
        end: QPointF,
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        super().__init__(parent)
        self._start = start
        self._end = end
        self._congestion_level: float = 0.0  # 0.0 = normal, 1.0 = fully congested

    def set_congestion(self, level: float) -> None:
        """Set road congestion visualization level (0-1)."""
        self._congestion_level = max(0.0, min(1.0, level))
        self.update()

    def boundingRect(self) -> QRectF:
        margin = 15
        x1 = min(self._start.x(), self._end.x()) - margin
        y1 = min(self._start.y(), self._end.y()) - margin
        x2 = max(self._start.x(), self._end.x()) + margin
        y2 = max(self._start.y(), self._end.y()) + margin
        return QRectF(x1, y1, x2 - x1, y2 - y1)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Road base (dark)
        pen = QPen(QColor(60, 60, 70), 20, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(self._start, self._end)

        # Road surface
        surface_color = QColor(80, 85, 95)
        if self._congestion_level > 0.3:
            # Blend toward red for congestion
            r = int(80 + 175 * self._congestion_level)
            g = int(85 - 30 * self._congestion_level)
            b = int(95 - 50 * self._congestion_level)
            surface_color = QColor(min(r, 255), max(g, 0), max(b, 0))

        pen2 = QPen(surface_color, 16, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen2)
        painter.drawLine(self._start, self._end)

        # Center line (dashed white)
        pen3 = QPen(QColor(200, 200, 200, 80), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen3)
        painter.drawLine(self._start, self._end)


class CityMapWidget(QGraphicsView):
    """
    Animated Digital Twin city map view.
    
    Displays:
    - 4 intersections (Junctions A-D)
    - Connecting roads
    - Moving vehicles
    - Traffic lights
    - Congestion indicators
    - Emergency route highlights
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Scene setup
        self._scene = QGraphicsScene(self)
        self._scene.setSceneRect(0, 0, 820, 620)
        self._scene.setBackgroundBrush(QBrush(QColor(18, 18, 24)))
        self.setScene(self._scene)

        # View settings
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("border: none; background: transparent;")
        self.setMinimumSize(400, 300)

        # Items
        self._intersections: dict[str, IntersectionItem] = {}
        self._roads: list[RoadItem] = []
        self._vehicles: list[VehicleItem] = []

        # Build the city map
        self._build_map()

        # Animation timer
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._animate)
        self._animation_timer.start(33)  # ~30 FPS

        # Vehicle spawn timer
        self._spawn_timer = QTimer(self)
        self._spawn_timer.timeout.connect(self._spawn_vehicles)
        self._spawn_timer.start(800)  # Spawn every 800ms

        # Title
        title = QGraphicsTextItem("CITY DIGITAL TWIN")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setDefaultTextColor(QColor(120, 180, 255, 180))
        title.setPos(300, 10)
        self._scene.addItem(title)

    def _build_map(self) -> None:
        """Build the static map elements."""
        # Create roads first (below intersections)
        for j1, j2 in ROAD_CONNECTIONS:
            p1 = JUNCTION_POSITIONS[j1]
            p2 = JUNCTION_POSITIONS[j2]
            road = RoadItem(p1, p2)
            self._scene.addItem(road)
            self._roads.append(road)

        # Create intersections
        for jid, pos in JUNCTION_POSITIONS.items():
            intersection = IntersectionItem(jid, pos)
            self._scene.addItem(intersection)
            self._intersections[jid] = intersection

        # Add grid decoration
        self._add_grid_decoration()

    def _add_grid_decoration(self) -> None:
        """Add subtle grid lines for visual depth."""
        pen = QPen(QColor(40, 40, 50, 30), 1, Qt.PenStyle.DotLine)
        for x in range(0, 850, 50):
            line = self._scene.addLine(x, 0, x, 620, pen)
        for y in range(0, 650, 50):
            line = self._scene.addLine(0, y, 820, y, pen)

    def update_junction(
        self,
        junction_id: str,
        vehicle_count: int,
        density_level: str,
        light_state: str,
        congestion: bool,
        emergency: bool,
    ) -> None:
        """Update a junction's visual state from controller data."""
        if junction_id in self._intersections:
            self._intersections[junction_id].update_status(
                vehicle_count, density_level, light_state,
                congestion, emergency,
            )

        # Update road congestion based on connected junctions
        for i, (j1, j2) in enumerate(ROAD_CONNECTIONS):
            if j1 == junction_id or j2 == junction_id:
                level = 0.0
                if congestion:
                    level = 0.8
                elif density_level == 'HIGH':
                    level = 0.4
                elif density_level == 'MEDIUM':
                    level = 0.15
                if i < len(self._roads):
                    self._roads[i].set_congestion(level)

    def _spawn_vehicles(self) -> None:
        """Spawn new vehicle items on random roads."""
        if len(self._vehicles) > 60:
            return

        # Pick a random road
        if not ROAD_CONNECTIONS:
            return

        j1, j2 = random.choice(ROAD_CONNECTIONS)
        p1 = JUNCTION_POSITIONS[j1]
        p2 = JUNCTION_POSITIONS[j2]

        # Random direction
        if random.random() > 0.5:
            start, end = p1, p2
        else:
            start, end = p2, p1

        # Check density for vehicle color
        intersection = self._intersections.get(j1)
        is_emg = random.random() < 0.03  # 3% emergency
        if is_emg:
            color = QColor(244, 67, 54)
        else:
            colors = [
                QColor(79, 195, 247),   # Light blue
                QColor(129, 199, 132),  # Light green
                QColor(255, 183, 77),   # Orange
                QColor(186, 104, 200),  # Purple
                QColor(255, 255, 255, 180),  # White
            ]
            color = random.choice(colors)

        vehicle = VehicleItem(start, end, color, is_emergency=is_emg)
        self._scene.addItem(vehicle)
        self._vehicles.append(vehicle)

    def _animate(self) -> None:
        """Animation tick — move vehicles and update effects."""
        # Move vehicles
        alive_vehicles = []
        for vehicle in self._vehicles:
            vehicle.advance_position()
            if vehicle.is_alive:
                alive_vehicles.append(vehicle)
            else:
                self._scene.removeItem(vehicle)
        self._vehicles = alive_vehicles

        # Animate intersections
        for intersection in self._intersections.values():
            intersection.advance_animation()

    def reset_map(self) -> None:
        """Clear all vehicles and reset junction state visualizers."""
        for vehicle in self._vehicles:
            try:
                self._scene.removeItem(vehicle)
            except Exception:
                pass
        self._vehicles.clear()

        for jid in self._intersections:
            self._intersections[jid].update_status(
                vehicle_count=0,
                density_level='LOW',
                light_state='RED',
                congestion=False,
                emergency=False
            )

        for road in self._roads:
            road.set_congestion(0.0)

    def resizeEvent(self, event) -> None:
        """Fit the scene in view on resize."""
        super().resizeEvent(event)
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
