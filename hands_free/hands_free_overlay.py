"""
hands_free/hands_free_overlay.py
Lightweight ULTRON HUD overlay for Hands-Free Mode.
"""
import threading

try:
    from PyQt6.QtWidgets import QWidget, QApplication
    from PyQt6.QtCore import Qt, pyqtSignal, QObject
    from PyQt6.QtGui import QColor, QPainter, QFont
    _HAS_QT = True
except ImportError:
    _HAS_QT = False


if _HAS_QT:
    class _Signals(QObject):
        update_sig = pyqtSignal(str, str)
        close_sig  = pyqtSignal()

    class _Widget(QWidget):
        def __init__(self):
            super().__init__()
            self._status = "STARTING"
            self._state  = "STARTING"
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Tool |
                Qt.WindowType.WindowTransparentForInput
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
            self.setFixedSize(300, 150)
            try:
                app = QApplication.instance()
                if app:
                    screen = app.primaryScreen().geometry()
                    self.move(20, screen.height() - 180)
            except Exception:
                self.move(20, 700)

        def set_status(self, msg, state):
            self._status = msg
            self._state  = state
            self.update()

        def paintEvent(self, event):
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            # Background
            p.setBrush(QColor(0, 10, 20, 215))
            p.setPen(QColor(0, 200, 255, 100))
            p.drawRoundedRect(0, 0, 300, 150, 10, 10)
            # Header bar
            p.setBrush(QColor(0, 170, 210, 180))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(0, 0, 300, 30, 10, 10)
            p.drawRect(0, 20, 300, 10)
            # Title
            p.setPen(QColor(0, 0, 0))
            p.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            p.drawText(10, 21, "ULTRON  HANDS-FREE MODE")
            # Status dot
            dot_color = QColor(0, 220, 100)
            if "EMERGENCY" in self._state:
                dot_color = QColor(220, 0, 0)
            elif self._state not in ("ACTIVE",):
                dot_color = QColor(0, 160, 220)
            p.setBrush(dot_color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(276, 10, 12, 12)
            # State line
            p.setPen(QColor(0, 200, 255))
            p.setFont(QFont("Consolas", 8))
            p.drawText(10, 52, "State: " + self._state)
            p.drawText(10, 70, "Gesture: " + self._status[:35])
            p.drawText(10, 88, "Index finger = cursor move")
            p.drawText(10, 106, "Pinch = click  |  Palm = media")
            # Footer
            p.setPen(QColor(0, 80, 100))
            p.setFont(QFont("Consolas", 6))
            p.drawText(10, 138, "Say: Ultron stop hand control")
            p.end()


class HandsFreeOverlay:
    def __init__(self):
        self._widget  = None
        self._signals = None

    def show(self):
        if not _HAS_QT:
            return
        try:
            app = QApplication.instance()
            if not app:
                return
            self._signals = _Signals()
            self._widget  = _Widget()
            self._signals.update_sig.connect(
                lambda m, s: self._widget.set_status(m, s)
            )
            self._signals.close_sig.connect(self._widget.hide)
            self._widget.show()
        except Exception as e:
            print(f"[HANDS-FREE] Overlay show error: {e}")

    def update_status(self, msg, state="ACTIVE"):
        if self._signals:
            try:
                self._signals.update_sig.emit(str(msg), str(state))
            except Exception:
                pass

    def close_overlay(self):
        if self._signals:
            try:
                self._signals.close_sig.emit()
            except Exception:
                pass
        self._widget  = None
        self._signals = None
