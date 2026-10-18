"""
hands_free/hands_free_manager.py
Main Hands-Free Mode controller.
"""
import threading
import time
import os
import logging
from typing import Optional

from .hands_free_state  import HandsFreeState, can_transition
from .hand_features     import HandFeatures
from .feature_extractor import extract_features
from .gesture_classifier import GestureClassifier
from .gesture_stabilizer import GestureStabilizer, GestureEvent
from .input_controller   import InputController
from .cursor_smoother    import CursorSmoother

logger = logging.getLogger("ultron.hands_free")

DEFAULT_CONFIG = {
    "camera_index":             0,
    "frame_width":              640,
    "frame_height":             480,
    "target_fps":               20,
    "min_detection_confidence": 0.65,
    "min_tracking_confidence":  0.60,
    "max_num_hands":            1,
    "mirrored":                 True,
    "cursor_sensitivity": 1.5,
    "cursor_smoothing":         0.70,
    "cursor_dead_zone": 0.008,
    "volume_step": 2,
    "screenshot_dir":           os.path.expanduser("~/Pictures/ULTRON_Screenshots"),
    "screenshot_hold_seconds":  5.0,
    "min_confidence":           0.55,
    "pinch_threshold":          0.35,
    "debug":                    True,
}


def _speak_safe(text):
    try:
        from modules.speaker import speak
        speak(text)
    except Exception:
        print(f"[HANDS-FREE TTS] {text}")


def _log(msg, level="info"):
    getattr(logger, level, logger.info)(msg)
    try:
        from modules.logger import log
        log(f"[HANDS-FREE] {msg}", level=level.upper())
    except Exception:
        pass


class HandsFreeManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = HandsFreeManager()
        return cls._instance

    def __init__(self, config=None):
        self._config     = {**DEFAULT_CONFIG, **(config or {})}
        self._state      = HandsFreeState.INACTIVE
        self._lock       = threading.Lock()
        self._stop_event = threading.Event()
        self._worker     = None

        self._classifier = GestureClassifier(self._config)
        self._stabilizer = GestureStabilizer(config=self._config)
        self._input      = InputController()
        self._smoother   = CursorSmoother(
            smoothing   = self._config["cursor_smoothing"],
            dead_zone   = self._config["cursor_dead_zone"],
            sensitivity = self._config["cursor_sensitivity"],
            mirrored    = self._config["mirrored"],
        )
        self._overlay = None

        self._three_finger_start = None
        self._screenshot_taken   = False
        self._stabilizer.add_callback(self._on_gesture_event)

    def _set_state(self, new_state):
        if can_transition(self._state, new_state):
            old = self._state
            self._state = new_state
            _log(f"State: {old.name} -> {new_state.name}")
            self._update_overlay(f"State: {new_state.name}", new_state.name)
        else:
            _log(f"Invalid transition {self._state.name}->{new_state.name}", "warning")

    @property
    def state(self):
        return self._state

    @property
    def is_active(self):
        return self._state in (HandsFreeState.ACTIVE, HandsFreeState.CALIBRATING)

    def enable(self):
        with self._lock:
            if self._state not in (HandsFreeState.INACTIVE, HandsFreeState.ERROR, HandsFreeState.EMERGENCY_STOPPED):
                _speak_safe("Hands-Free Mode is already active Sir.")
                return True
            self._set_state(HandsFreeState.STARTING)
        _speak_safe("Activating Hands-Free Mode Sir. Please show your hand.")
        self._stop_event.clear()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True, name="HandsFreeWorker")
        self._worker.start()
        self._init_overlay()
        return True

    def disable(self, reason="user command"):
        with self._lock:
            if self._state == HandsFreeState.INACTIVE:
                return True
            self._set_state(HandsFreeState.STOPPING)
        _log(f"Disabling: {reason}")
        self._stop_event.set()
        self._input.pause()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=4.0)
        with self._lock:
            self._state = HandsFreeState.INACTIVE
        self._close_overlay()
        _speak_safe("Hands-Free Mode deactivated Sir.")
        return True

    def emergency_stop(self):
        _log("EMERGENCY STOP", "warning")
        self._input.emergency_stop()
        self._stop_event.set()
        with self._lock:
            self._state = HandsFreeState.EMERGENCY_STOPPED
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=3.0)
        self._close_overlay()
        _speak_safe("Emergency stop activated Sir.")

    def pause(self):
        self._input.pause()
        with self._lock:
            if can_transition(self._state, HandsFreeState.PAUSED):
                self._state = HandsFreeState.PAUSED
        _speak_safe("Hands-Free Mode paused Sir.")

    def resume(self):
        self._input.arm()
        with self._lock:
            if can_transition(self._state, HandsFreeState.ACTIVE):
                self._state = HandsFreeState.ACTIVE
        _speak_safe("Hands-Free Mode resumed Sir.")

    def status(self):
        return self._state.name



    def handle_media(self, cmd: str):
        """Handle voice media commands."""
        try:
            import pyautogui
            actions = {
                "play":       lambda: pyautogui.press("playpause"),
                "pause":      lambda: pyautogui.press("playpause"),
                "playpause":  lambda: pyautogui.press("playpause"),
                "stop":       lambda: pyautogui.press("stop"),
                "next":       lambda: pyautogui.press("nexttrack"),
                "prev":       lambda: pyautogui.press("prevtrack"),
                "forward10":  lambda: pyautogui.press("right"),
                "back10":     lambda: pyautogui.press("left"),
                "mute":       lambda: pyautogui.press("volumemute"),
                "fullscreen": lambda: pyautogui.press("f"),
                "volup":      lambda: [pyautogui.press("volumeup") for _ in range(2)],
                "voldown":    lambda: [pyautogui.press("volumedown") for _ in range(2)],
            }
            if cmd in actions:
                actions[cmd]()
                print(f"[HANDS-FREE] MEDIA: {cmd}")
                try:
                    from modules.speaker import speak
                    speak(f"{cmd} Sir.")
                except Exception: pass
        except Exception as e:
            print(f"[HANDS-FREE] media error: {e}")
    def show_desktop(self):
        try:
            import pyautogui
            pyautogui.hotkey("win", "d")
            print("[HANDS-FREE] SHOW DESKTOP")
        except Exception as e:
            print(f"[HANDS-FREE] show_desktop error: {e}")

    def type_text(self, text: str):
        if not text: return
        print(f"[HANDS-FREE] TYPING: {text}")
        try:
            from modules.speaker import speak
            speak(f"Typing {text} Sir.")
        except Exception: pass
        try:
            import time as _t
            import pyautogui
            _t.sleep(0.4)
            pyautogui.typewrite(text, interval=0.05)
        except Exception as e:
            print(f"[HANDS-FREE] type_text error: {e}")
            try:
                import pyperclip, pyautogui
                pyperclip.copy(text)
                pyautogui.hotkey("ctrl", "v")
            except Exception: pass
    def calibrate(self):
        _speak_safe("Place your hand in the center of the camera Sir.")

    def _worker_loop(self):
        try:
            import cv2
        except ImportError:
            self._set_state(HandsFreeState.ERROR)
            _speak_safe("Error: OpenCV not installed Sir.")
            return
        try:
            import mediapipe as mp
            mp_hands = mp.solutions.hands
        except ImportError:
            self._set_state(HandsFreeState.ERROR)
            _speak_safe("Error: MediaPipe not installed Sir.")
            return

        cap = None
        try:
            cap = cv2.VideoCapture(self._config["camera_index"])
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self._config["frame_width"])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config["frame_height"])
            cap.set(cv2.CAP_PROP_FPS,          self._config["target_fps"])
            if not cap.isOpened():
                raise RuntimeError("Camera not available")
        except Exception as e:
            _log(f"Camera error: {e}", "error")
            self._set_state(HandsFreeState.CAMERA_UNAVAILABLE)
            _speak_safe("Camera unavailable Sir.")
            return

        try:
            hands_detector = mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=self._config["max_num_hands"],
                min_detection_confidence=self._config["min_detection_confidence"],
                min_tracking_confidence=self._config["min_tracking_confidence"],
                model_complexity=0,
            )
        except Exception as e:
            _log(f"MediaPipe init error: {e}", "error")
            self._set_state(HandsFreeState.ERROR)
            if cap: cap.release()
            return

        self._set_state(HandsFreeState.ACTIVE)
        self._input.arm()
        self._smoother.reset()
        _speak_safe("Hands-Free Mode active Sir. Show your hand to move the cursor.")
        self._update_overlay("Show hand â€” index tip moves cursor", "ACTIVE")

        target_interval = 1.0 / max(1, self._config["target_fps"])
        _log("Worker loop started")

        try:
            while not self._stop_event.is_set():
                t_start = time.time()

                ret, frame = cap.read()
                if not ret or frame is None:
                    time.sleep(0.05)
                    continue

                if self._state not in (HandsFreeState.ACTIVE, HandsFreeState.PAUSED):
                    time.sleep(0.05)
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_rgb.flags.writeable = False
                result = hands_detector.process(frame_rgb)
                frame_rgb.flags.writeable = True

                features = extract_features(result, mirrored=self._config["mirrored"])

                if features and features.is_valid(self._config["min_confidence"]):
                    # CURSOR: move with ANY hand â€” uses index fingertip
                    if self._state == HandsFreeState.ACTIVE:
                        sx, sy = self._smoother.update(
                            features.index_tip[0],
                            features.index_tip[1]
                        )
                        self._input.move_cursor(sx, sy)

                    # GESTURE: classify for actions
                    raw_gesture = self._classifier.classify(features)
                    self._stabilizer.update(raw_gesture, features.confidence)

                    # Three-finger screenshot
                    if raw_gesture == "THREE_FINGER":
                        self._handle_three_finger_hold(features)
                    else:
                        self._three_finger_start = None
                        self._screenshot_taken   = False

                    self._update_overlay(
                        f"{raw_gesture} | {features.confidence:.0%}",
                        "ACTIVE"
                    )
                else:
                    self._smoother.reset()
                    self._three_finger_start = None
                    self._screenshot_taken   = False
                    self._update_overlay("No hand â€” show your hand", "ACTIVE")

                elapsed = time.time() - t_start
                sleep   = target_interval - elapsed
                if sleep > 0:
                    time.sleep(sleep)

        except Exception as e:
            _log(f"Worker exception: {e}", "error")
            self._set_state(HandsFreeState.ERROR)
        finally:
            try: hands_detector.close()
            except Exception: pass
            try: cap.release()
            except Exception: pass
            self._input.pause()
            _log("Worker loop ended, camera released")

    def _on_gesture_event(self, event):
        if self._state != HandsFreeState.ACTIVE:
            return
        g = event.gesture
        _log(f"Gesture action: {g}") if g != "INDEX_POINT" else None
        if g == "PINCH":
            self._input.left_click()
            _speak_safe("Click.")
            print("[HANDS-FREE] LEFT CLICK")
        elif g == "TWO_FINGER":
            self._input.left_click()
            print("[HANDS-FREE] LEFT CLICK")
        elif g == "OPEN_PALM":
            self._input.media_play_pause()
            print("[HANDS-FREE] PLAY/PAUSE")
        elif g == "FIST":
            self._input.media_play_pause()
            print("[HANDS-FREE] MEDIA CONTROL")
        elif g == "THUMBS_UP":
            self._input.volume_up(self._config.get("volume_step", 5))
            print("[HANDS-FREE] VOLUME UP")
        elif g == "THUMBS_DOWN":
            self._input.volume_down(self._config.get("volume_step", 5))
            print("[HANDS-FREE] VOLUME DOWN")
        elif g == "PINKY_UP":
            self._input.scroll(3)
            print("[HANDS-FREE] SCROLL UP")
        elif g == "PINKY_DOWN":
            self._input.scroll(-3)
            print("[HANDS-FREE] SCROLL DOWN")

    def _handle_three_finger_hold(self, features):
        if self._screenshot_taken: return
        now = time.time()
        if self._three_finger_start is None:
            self._three_finger_start = now
        hold   = now - self._three_finger_start
        target = self._config.get("screenshot_hold_seconds", 5.0)
        if hold >= target:
            self._take_screenshot()
        else:
            self._update_overlay(f"Screenshot in {target-hold:.0f}s...", "ACTIVE")

    def _take_screenshot(self):
        self._screenshot_taken = True
        save_dir = self._config.get("screenshot_dir", os.path.expanduser("~/Pictures"))
        os.makedirs(save_dir, exist_ok=True)
        from datetime import datetime
        fname = f"ultron_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        save_path = os.path.join(save_dir, fname)
        success = self._input.screenshot(save_path)
        if success:
            _speak_safe("Screenshot saved Sir.")
            _log(f"Screenshot: {save_path}")
        else:
            _log("Screenshot failed", "error")

    def _init_overlay(self):
        try:
            from .hands_free_overlay import HandsFreeOverlay
            self._overlay = HandsFreeOverlay()
            self._overlay.show()
        except Exception as e:
            _log(f"Overlay init failed: {e}", "warning")

    def _update_overlay(self, msg, state=None):
        if self._overlay:
            try:
                self._overlay.update_status(msg, state or self._state.name)
            except Exception:
                pass

    def _close_overlay(self):
        if self._overlay:
            try: self._overlay.close_overlay()
            except Exception: pass
            self._overlay = None








