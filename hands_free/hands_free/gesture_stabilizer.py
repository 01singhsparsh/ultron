"""
hands_free/gesture_stabilizer.py
Temporal gesture stabilization engine with cooldowns, debounce, hold detection.
"""
import time
from collections import deque
from typing import Optional, Callable, Dict, Any


class GestureEvent:
    """Fired when a stable gesture is confirmed."""
    def __init__(self, gesture: str, hold_ms: float, confidence: float):
        self.gesture    = gesture
        self.hold_ms    = hold_ms
        self.confidence = confidence
        self.timestamp  = time.time()


class GestureStabilizer:
    """
    Stabilizes gesture classification using:
    - Frame history (majority voting)
    - Minimum stable frame count
    - Hold duration tracking
    - Per-gesture cooldowns
    - Debounce
    """

    GESTURE_CONFIG: Dict[str, Dict[str, Any]] = {
        "INDEX_POINT":  {"min_frames": 3,  "cooldown_ms": 0,    "min_hold_ms": 0,    "priority": 1},
        "PINCH":        {"min_frames": 5,  "cooldown_ms": 600,  "min_hold_ms": 80,   "priority": 5},
        "TWO_FINGER":   {"min_frames": 6,  "cooldown_ms": 800,  "min_hold_ms": 200,  "priority": 4},
        "OPEN_PALM":    {"min_frames": 8,  "cooldown_ms": 1200, "min_hold_ms": 400,  "priority": 3},
        "FIST":         {"min_frames": 8,  "cooldown_ms": 1200, "min_hold_ms": 400,  "priority": 3},
        "THUMBS_UP":    {"min_frames": 6,  "cooldown_ms": 900,  "min_hold_ms": 300,  "priority": 4},
        "THUMBS_DOWN":  {"min_frames": 6,  "cooldown_ms": 900,  "min_hold_ms": 300,  "priority": 4},
        "PINKY_UP":     {"min_frames": 5,  "cooldown_ms": 400,  "min_hold_ms": 150,  "priority": 2},
        "PINKY_DOWN":   {"min_frames": 5,  "cooldown_ms": 400,  "min_hold_ms": 150,  "priority": 2},
        "THREE_FINGER": {"min_frames": 10, "cooldown_ms": 8000, "min_hold_ms": 5000, "priority": 6},
        "NONE":         {"min_frames": 2,  "cooldown_ms": 0,    "min_hold_ms": 0,    "priority": 0},
    }

    def __init__(self, history_size: int = 12, config: dict = None):
        self._history     = deque(maxlen=history_size)
        self._config      = config or {}
        self._current     = "NONE"
        self._candidate   = "NONE"
        self._stable_count = 0
        self._gesture_start: Dict[str, float] = {}
        self._last_triggered: Dict[str, float] = {}
        self._hold_start: Optional[float] = None
        self._on_gesture_callbacks: list = []

    def add_callback(self, fn: Callable[[GestureEvent], None]):
        self._on_gesture_callbacks.append(fn)

    def update(self, raw_gesture: str, confidence: float) -> Optional[GestureEvent]:
        """Feed a new raw gesture classification. Returns a GestureEvent if fired."""
        self._history.append(raw_gesture)
        now = time.time() * 1000  # ms

        # Majority vote from history
        if len(self._history) >= 3:
            counts = {}
            for g in self._history:
                counts[g] = counts.get(g, 0) + 1
            majority = max(counts, key=counts.get)
        else:
            majority = raw_gesture

        cfg = self.GESTURE_CONFIG.get(majority, {"min_frames": 5, "cooldown_ms": 500, "min_hold_ms": 0, "priority": 1})

        # Track stable frames
        if majority == self._candidate:
            self._stable_count += 1
        else:
            self._candidate    = majority
            self._stable_count = 1
            self._hold_start   = time.time() * 1000

        # Check if candidate is stable enough
        if self._stable_count < cfg["min_frames"]:
            return None

        # Check hold duration
        hold_elapsed = now - (self._hold_start or now)
        if hold_elapsed < cfg["min_hold_ms"]:
            return None

        # Check cooldown
        last = self._last_triggered.get(majority, 0)
        if (now - last) < cfg["cooldown_ms"]:
            return None

        # Don't re-fire same gesture unless it was reset
        if majority == self._current and majority != "INDEX_POINT":
            return None

        # Fire event
        self._current = majority
        if majority != "NONE":
            self._last_triggered[majority] = now
            event = GestureEvent(majority, hold_elapsed, confidence)
            for cb in self._on_gesture_callbacks:
                try:
                    cb(event)
                except Exception:
                    pass
            return event

        # Reset current on NONE
        self._current = "NONE"
        return None

    @property
    def current_gesture(self) -> str:
        return self._candidate

    @property
    def hold_duration_ms(self) -> float:
        if self._hold_start is None:
            return 0.0
        return time.time() * 1000 - self._hold_start

    def reset(self):
        self._history.clear()
        self._current      = "NONE"
        self._candidate    = "NONE"
        self._stable_count = 0
        self._hold_start   = None
