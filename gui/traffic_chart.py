"""
Traffic Chart Widget for SmartCity Twin.
Draws a real-time line chart of vehicle counts for each junction.
"""

from __future__ import annotations

import collections
from typing import Optional

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPainterPath


class TrafficChartWidget(QWidget):
    """
    A lightweight custom line chart drawn with QPainter.
    Shows the history of vehicle counts across multiple junctions.
    """

    def __init__(self, max_history: int = 100, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.max_history = max_history
        self.setMinimumHeight(150)
        
        # History buffers for each node
        self._data: dict[str, collections.deque] = {
            'junction_a': collections.deque(maxlen=max_history),
            'junction_b': collections.deque(maxlen=max_history),
            'junction_c': collections.deque(maxlen=max_history),
            'junction_d': collections.deque(maxlen=max_history),
        }
        
        # Colors for each node (matching the image theme roughly)
        self._colors = {
            'junction_a': QColor(3, 169, 244),   # Light Blue
            'junction_b': QColor(38, 166, 154),  # Teal/Green
            'junction_c': QColor(255, 160, 0),   # Orange
            'junction_d': QColor(239, 83, 80),   # Red
        }
        
        self._labels = {
            'junction_a': 'Junction A',
            'junction_b': 'Junction B',
            'junction_c': 'Junction C',
            'junction_d': 'Junction D',
        }
        
        # Background and grid colors
        self._bg_color = QColor(17, 17, 34)
        self._grid_color = QColor(42, 42, 74)
        self._text_color = QColor(136, 136, 170)

    def add_data(self, data: dict[str, int]) -> None:
        """
        Add a new data point for each junction.
        data = {'junction_a': 10, 'junction_b': 5, ...}
        """
        for node_id, value in data.items():
            if node_id in self._data:
                self._data[node_id].append(value)
        self.update()  # Trigger a repaint
        
    def reset_data(self) -> None:
        """Clear the chart history."""
        for q in self._data.values():
            q.clear()
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Fill background
        painter.fillRect(rect, self._bg_color)
        
        # Determine max value for Y-axis scaling
        max_val = 10
        for q in self._data.values():
            if q:
                max_val = max(max_val, max(q))
                
        # Add some padding to max_val
        max_val = int(max_val * 1.2)
        if max_val < 10:
            max_val = 10
            
        # Margins
        margin_left = 40
        margin_right = 10
        margin_top = 30
        margin_bottom = 20
        
        chart_rect = QRectF(
            margin_left, 
            margin_top, 
            rect.width() - margin_left - margin_right, 
            rect.height() - margin_top - margin_bottom
        )
        
        # Draw Title
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(
            int(chart_rect.center().x() - 80), 
            20, 
            "Vehicle History (Last 100 Samples)"
        )
        
        # Draw Grid & Y-axis labels
        painter.setFont(QFont("Segoe UI", 7))
        grid_pen = QPen(self._grid_color, 1)
        grid_pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(grid_pen)
        
        y_steps = 5
        for i in range(y_steps + 1):
            y_ratio = i / y_steps
            y_pos = chart_rect.bottom() - (y_ratio * chart_rect.height())
            
            # Grid line
            painter.drawLine(
                int(chart_rect.left()), int(y_pos), 
                int(chart_rect.right()), int(y_pos)
            )
            
            # Label
            painter.setPen(self._text_color)
            val = int(max_val * y_ratio)
            painter.drawText(
                5, int(y_pos + 4), 
                f"{val}"
            )
            painter.setPen(grid_pen) # restore grid pen
            
        # Draw lines
        for node_id, queue in self._data.items():
            if not queue:
                continue
                
            path = QPainterPath()
            n_points = len(queue)
            
            # Calculate x step
            if self.max_history > 1:
                x_step = chart_rect.width() / (self.max_history - 1)
            else:
                x_step = 0
                
            # Start x at the right-aligned position (if queue is not full)
            start_idx = self.max_history - n_points
            
            for i, val in enumerate(queue):
                x = chart_rect.left() + (start_idx + i) * x_step
                y = chart_rect.bottom() - (val / max_val) * chart_rect.height()
                
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
                    
            pen = QPen(self._colors[node_id], 2)
            painter.setPen(pen)
            painter.drawPath(path)
            
        # Draw Legend
        legend_x = margin_left + 10
        legend_y = margin_top + 10
        painter.setFont(QFont("Segoe UI", 8))
        
        for node_id, label in self._labels.items():
            # Line segment
            painter.setPen(QPen(self._colors[node_id], 2))
            painter.drawLine(int(legend_x), int(legend_y - 4), int(legend_x + 15), int(legend_y - 4))
            
            # Text
            painter.setPen(self._text_color)
            painter.drawText(int(legend_x + 20), int(legend_y), label)
            
            legend_y += 15

