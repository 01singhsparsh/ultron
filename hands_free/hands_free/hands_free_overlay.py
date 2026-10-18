"""
hands_free/hands_free_overlay.py
Lightweight ULTRON-style HUD overlay for Hands-Free Mode.
Uses PyQt6. Click-through. Does not steal focus.
"""
import threading
from typing import Optional

try:
    from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
    from PyQt6.QtCore    import Qt, QTimer, pyqtSignal, QObject
    from PyQt6.QtGui     import QColor, QPainter, QFont
    _HAS_QT = True
except ImportError:
    _HAS_QT = False


if _HAS_QT:
    class _OverlaySignals(QObject):
        update_signal = pyqtSignal(str, str)
        close_signal  = pyqtSignal()

    class _OverlayWidget(QWidget):
        def __init__(self):
            super().__init__()
            self._status = "INITIALIZING"
            self._state  = "STARTING"
            self._build_ui()

        def _build_ui(self):
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Tool |
                Qt.WindowType.WindowTransparentForInput
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
            self.setFixedSize(280, 140)

            # Position bottom-left
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().geometry()
            self.move(20, screen.height() - 170)

        def paintEvent(self, event):
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Background
            p.setBrush(QColor(0, 10, 20, 210))
            p.setPen(QColor(0, 200, 255, 120))
            p.drawRoundedRect(0, 0, 280, 140, 10, 10)

            # Title bar accent
            p.setBrush(QColor(0, 180, 220, 180))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(0, 0, 280, 28, 10, 10)
            p.drawRect(0, 18, 280, 10)

            # Title text
            p.setPen(QColor(0, 0, 0))
            p.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            p.drawText(10, 20, "ULTRON  HANDS-FREE")

            # State badge
            color = QColor(0, 220, 100) if self._state == "ACTIVE" else                     QColor(220, 80, 0) if "EMERGENCY" in self._state else                     QColor(0, 160, 220)
            p.setBrush(color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(248, 8, 10, 10)

            # Status text
            p.setPen(QColor(0, 200, 255))
            p.setFont(QFont("Consolas", 8))
            p.drawText(10, 48, f"● State: {self._state}")
            p.drawText(10, 66, "● Gesture recognition: ON")

            # Bottom message
            p.setPen(QColor(0, 150, 180))
            p.setFont(QFont("Consolas", 7))
            lines = self._status[:60].split("
")
            y = 90
            for line in lines[:3]:
                p.drawText(10, y, line)
                y += 16

            # Footer
            p.setPen(QColor(0, 80, 100))
            p.setFont(QFont("Consolas", 6))
            p.drawText(10, 132, "Say: 'Ultron stop hand control' to exit")

            p.end()

        def set_status(self, msg: str, state: str):
            self._status = msg
            self._state  = state
            self.update()


class HandsFreeOverlay:
    """Thread-safe overlay wrapper."""

    def __init__(self):
        self._widget: Optional[object] = None
        self._signals = None

    def show(self):
        if not _HAS_QT:
            return
        try:
            app = QApplication.instance()
            if not app:
                return
            self._signals = _OverlaySignals()
            self._widget  = _OverlayWidget()
            self._signals.update_signal.connect(
                lambda msg, state: self._widget.set_status(msg, state)
            )
            self._signals.close_signal.connect(self._widget.hide)
            self._widget.show()
        except Exception as e:
            pass

    def update_status(self, msg: str, state: str = "ACTIVE"):
        if self._signals:
            try:
                self._signals.update_signal.emit(msg, state)
            except Exception:
                pass

    def close_overlay(self):
        if self._signals:
            try:
                self._signals.close_signal.emit()
            except Exception:
                pass
        self._widget = None
        self._signals = None
