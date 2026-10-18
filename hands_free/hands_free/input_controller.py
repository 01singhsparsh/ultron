"""
hands_free/input_controller.py
Abstraction layer for mouse/keyboard/media input.
Stops all input on emergency stop or lock.
"""
import time
import threading
import ctypes
import subprocess
from typing import Tuple

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    _HAS_PYAUTOGUI = True
except ImportError:
    _HAS_PYAUTOGUI = False


class InputController:
    """
    Thread-safe input abstraction.
    All methods check the lock state before executing.
    """

    def __init__(self):
        self._locked     = True   # Start locked until armed
        self._emergency  = False
        self._lock       = threading.Lock()
        self._screen_w   = 1920
        self._screen_h   = 1080
        self._last_move  = 0.0
        self._move_rate  = 1.0 / 60   # max 60 moves/sec
        self._update_screen_size()

    def _update_screen_size(self):
        try:
            if _HAS_PYAUTOGUI:
                self._screen_w, self._screen_h = pyautogui.size()
        except Exception:
            pass

    def _can_act(self) -> bool:
        with self._lock:
            return not self._locked and not self._emergency

    def arm(self):
        """Unlock cursor control."""
        with self._lock:
            self._locked   = False
            self._emergency = False

    def pause(self):
        with self._lock:
            self._locked = True

    def resume(self):
        with self._lock:
            if not self._emergency:
                self._locked = False

    def emergency_stop(self):
        with self._lock:
            self._locked   = True
            self._emergency = True

    def reset_emergency(self):
        with self._lock:
            self._emergency = False
            self._locked    = True

    def move_cursor(self, x: float, y: float):
        if not self._can_act():
            return
        now = time.time()
        if now - self._last_move < self._move_rate:
            return
        self._last_move = now
        try:
            px = int(max(0, min(x * self._screen_w, self._screen_w - 1)))
            py = int(max(0, min(y * self._screen_h, self._screen_h - 1)))
            if _HAS_PYAUTOGUI:
                pyautogui.moveTo(px, py, duration=0)
        except Exception:
            pass

    def left_click(self):
        if not self._can_act():
            return
        try:
            if _HAS_PYAUTOGUI:
                pyautogui.click()
        except Exception:
            pass

    def right_click(self):
        if not self._can_act():
            return
        try:
            if _HAS_PYAUTOGUI:
                pyautogui.rightClick()
        except Exception:
            pass

    def scroll(self, amount: int):
        if not self._can_act():
            return
        try:
            if _HAS_PYAUTOGUI:
                pyautogui.scroll(amount)
        except Exception:
            pass

    def media_play_pause(self):
        if not self._can_act():
            return
        try:
            if _HAS_PYAUTOGUI:
                pyautogui.press("playpause")
        except Exception:
            pass

    def volume_up(self, step: int = 5):
        if not self._can_act():
            return
        try:
            for _ in range(max(1, step // 2)):
                if _HAS_PYAUTOGUI:
                    pyautogui.press("volumeup")
        except Exception:
            pass

    def volume_down(self, step: int = 5):
        if not self._can_act():
            return
        try:
            for _ in range(max(1, step // 2)):
                if _HAS_PYAUTOGUI:
                    pyautogui.press("volumedown")
        except Exception:
            pass

    def screenshot(self, save_path: str) -> bool:
        try:
            if _HAS_PYAUTOGUI:
                img = pyautogui.screenshot()
                img.save(save_path)
                return True
        except Exception:
            pass
        try:
            import subprocess
            subprocess.Popen(["snippingtool", "/clip"], creationflags=0x08000000)
            return True
        except Exception:
            return False

    @property
    def is_armed(self) -> bool:
        with self._lock:
            return not self._locked and not self._emergency

    @property
    def is_emergency(self) -> bool:
        with self._lock:
            return self._emergency
