"""
hands_free/hands_free_manager.py
Main Hands-Free Mode controller. Integrates camera, MediaPipe,
gesture pipeline, input controller, and overlay.
"""
import threading
import time
import os
import sys
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


# ── Default configuration ──
DEFAULT_CONFIG = {
    "camera_index":             0,
    "frame_width":              640,
    "frame_height":             480,
    "target_fps":               20,
    "min_detection_confidence": 0.70,
    "min_tracking_confidence":  0.65,
    "max_num_hands":            1,
    "mirrored":                 True,
    "cursor_sensitivity":       1.0,
    "cursor_smoothing":         0.65,
    "cursor_dead_zone":         0.02,
    "volume_step":              5,
    "screenshot_dir":           os.path.expanduser("~/Pictures/ULTRON_Screenshots"),
    "screenshot_hold_seconds":  5.0,
    "gesture_cooldown_ms":      700,
    "min_confidence":           0.60,
    "pinch_threshold":          0.35,
    "debug":                    False,
}


def _speak_safe(text: str):
    """Try to use ULTRON TTS, fallback silently."""
    try:
        from modules.speaker import speak
        speak(text)
    except Exception:
        logger.info(f"[ULTRON TTS] {text}")


def _log(msg: str, level: str = "info"):
    getattr(logger, level, logger.info)(msg)
    try:
        from modules.logger import log
        log(f"[HANDS-FREE] {msg}", level=level.upper())
    except Exception:
        pass


class HandsFreeManager:
    """
    Singleton-style manager for Hands-Free Mode.
    Call enable() to start, disable() to stop.
    """

    _instance: Optional["HandsFreeManager"] = None

    @classmethod
    def get_instance(cls) -> "HandsFreeManager":
        if cls._instance is None:
            cls._instance = HandsFreeManager()
        return cls._instance

    def __init__(self, config: dict = None):
        self._config     = {**DEFAULT_CONFIG, **(config or {})}
        self._state      = HandsFreeState.INACTIVE
        self._lock       = threading.Lock()
        self._stop_event = threading.Event()
        self._worker: Optional[threading.Thread] = None

        # Sub-systems
        self._classifier = GestureClassifier(self._config)
        self._stabilizer = GestureStabilizer(config=self._config)
        self._input      = InputController()
        self._smoother   = CursorSmoother(
            smoothing   = self._config["cursor_smoothing"],
            dead_zone   = self._config["cursor_dead_zone"],
            sensitivity = self._config["cursor_sensitivity"],
            mirrored    = self._config["mirrored"],
        )
        self._overlay    = None  # lazy init

        # Screenshot state
        self._three_finger_start: Optional[float] = None
        self._screenshot_taken = False

        # Pinch click state
        self._pinch_active = False

        # Register gesture callback
        self._stabilizer.add_callback(self._on_gesture_event)

    # ─── State management ───────────────────────────────────────

    def _set_state(self, new_state: HandsFreeState):
        if can_transition(self._state, new_state):
            old = self._state
            self._state = new_state
            _log(f"State: {old.name} → {new_state.name}")
            self._update_overlay(f"State: {new_state.name}")
        else:
            _log(f"Invalid transition {self._state.name}→{new_state.name}", "warning")

    @property
    def state(self) -> HandsFreeState:
        return self._state

    @property
    def is_active(self) -> bool:
        return self._state in (HandsFreeState.ACTIVE, HandsFreeState.CALIBRATING)

    # ─── Public API ─────────────────────────────────────────────

    def enable(self) -> bool:
        """Activate Hands-Free Mode. Idempotent."""
        with self._lock:
            if self._state not in (HandsFreeState.INACTIVE, HandsFreeState.ERROR, HandsFreeState.EMERGENCY_STOPPED):
                _speak_safe("Hands-Free Mode is already active Sir.")
                return True
            self._set_state(HandsFreeState.STARTING)

        _speak_safe("Activating Hands-Free Mode Sir. Please show your hand.")
        self._stop_event.clear()
        self._worker = threading.Thread(
            target=self._worker_loop, daemon=True, name="HandsFreeWorker"
        )
        self._worker.start()
        self._init_overlay()
        return True

    def disable(self, reason: str = "user command") -> bool:
        """Deactivate Hands-Free Mode. Idempotent."""
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
        """Immediately stop all gesture input."""
        _log("EMERGENCY STOP", "warning")
        self._input.emergency_stop()
        self._stop_event.set()

        with self._lock:
            self._state = HandsFreeState.EMERGENCY_STOPPED

        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=3.0)

        self._close_overlay()
        _speak_safe("Emergency stop activated. All gesture control disabled Sir.")

    def pause(self):
        self._input.pause()
        with self._lock:
            if can_transition(self._state, HandsFreeState.PAUSED):
                self._state = HandsFreeState.PAUSED
        _speak_safe("Hands-Free Mode paused Sir.")
        self._update_overlay("PAUSED")

    def resume(self):
        self._input.arm()
        with self._lock:
            if can_transition(self._state, HandsFreeState.ACTIVE):
                self._state = HandsFreeState.ACTIVE
        _speak_safe("Hands-Free Mode resumed Sir.")
        self._update_overlay("ACTIVE")

    def status(self) -> str:
        return self._state.name

    def calibrate(self):
        _speak_safe("Starting calibration. Please position your hand in the center of the camera.")
        self._update_overlay("CALIBRATING — Place hand center")

    # ─── Worker loop ────────────────────────────────────────────

    def _worker_loop(self):
        """Main camera + gesture processing thread."""
        cv2 = None
        cap = None
        mp_hands = None
        hands    = None

        try:
            import cv2 as _cv2
            cv2 = _cv2
        except ImportError:
            _log("OpenCV not installed", "error")
            self._set_state(HandsFreeState.ERROR)
            _speak_safe("Error: OpenCV is not installed Sir.")
            return

        try:
            import mediapipe as mp
            mp_hands = mp.solutions.hands
        except ImportError:
            _log("MediaPipe not installed", "error")
            self._set_state(HandsFreeState.ERROR)
            _speak_safe("Error: MediaPipe is not installed Sir.")
            return

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
            _speak_safe("Camera unavailable Sir. Please check your webcam.")
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
            cap.release()
            return

        self._set_state(HandsFreeState.ACTIVE)
        self._input.arm()
        self._smoother.reset()
        _speak_safe("Hands-Free Mode active Sir. Move your index finger to control the cursor.")
        self._update_overlay("ACTIVE — Index finger = cursor")

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

                # MediaPipe processing (RGB)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_rgb.flags.writeable = False
                result = hands_detector.process(frame_rgb)
                frame_rgb.flags.writeable = True

                # Extract features
                features = extract_features(result, mirrored=self._config["mirrored"])

                if features and features.is_valid(self._config["min_confidence"]):
                    # Classify gesture
                    raw_gesture = self._classifier.classify(features)
                    # Stabilize
                    self._stabilizer.update(raw_gesture, features.confidence)

                    # Always update cursor (INDEX_POINT handled continuously)
                    if raw_gesture == "INDEX_POINT" and self._state == HandsFreeState.ACTIVE:
                        sx, sy = self._smoother.update(
                            features.index_tip[0], features.index_tip[1]
                        )
                        self._input.move_cursor(sx, sy)

                    # Three-finger screenshot countdown
                    if raw_gesture == "THREE_FINGER":
                        self._handle_three_finger_hold(features)
                    else:
                        self._three_finger_start = None
                        self._screenshot_taken   = False

                    # Update overlay
                    if self._config["debug"]:
                        self._update_overlay(
                            f"Gesture: {raw_gesture} ({features.confidence:.0%})"
                        )
                else:
                    self._smoother.reset()
                    self._three_finger_start = None
                    self._screenshot_taken   = False

                # Rate limit
                elapsed = time.time() - t_start
                sleep   = target_interval - elapsed
                if sleep > 0:
                    time.sleep(sleep)

        except Exception as e:
            _log(f"Worker exception: {e}", "error")
            self._set_state(HandsFreeState.ERROR)
        finally:
            try:
                hands_detector.close()
            except Exception:
                pass
            try:
                cap.release()
            except Exception:
                pass
            self._input.pause()
            _log("Worker loop ended, camera released")

    # ─── Gesture event handler ───────────────────────────────────

    def _on_gesture_event(self, event: GestureEvent):
        """Called by stabilizer when a confirmed gesture fires."""
        if self._state != HandsFreeState.ACTIVE:
            return

        g = event.gesture
        _log(f"Gesture fired: {g}")

        if g == "PINCH":
            self._input.left_click()
            self._update_overlay("● LEFT CLICK")

        elif g == "TWO_FINGER":
            self._input.right_click()
            self._update_overlay("● RIGHT CLICK")

        elif g == "OPEN_PALM":
            self._input.media_play_pause()
            self._update_overlay("● PLAY/PAUSE")

        elif g == "FIST":
            self._input.media_play_pause()
            self._update_overlay("● MEDIA CONTROL")

        elif g == "THUMBS_UP":
            self._input.volume_up(self._config.get("volume_step", 5))
            self._update_overlay("● VOLUME UP")

        elif g == "THUMBS_DOWN":
            self._input.volume_down(self._config.get("volume_step", 5))
            self._update_overlay("● VOLUME DOWN")

        elif g == "PINKY_UP":
            self._input.scroll(3)
            self._update_overlay("● SCROLL UP")

        elif g == "PINKY_DOWN":
            self._input.scroll(-3)
            self._update_overlay("● SCROLL DOWN")

    # ─── Three-finger screenshot ─────────────────────────────────

    def _handle_three_finger_hold(self, features: HandFeatures):
        if self._screenshot_taken:
            return
        now = time.time()
        if self._three_finger_start is None:
            self._three_finger_start = now
        hold   = now - self._three_finger_start
        target = self._config.get("screenshot_hold_seconds", 5.0)
        remaining = max(0, target - hold)

        if remaining > 0:
            if int(remaining) != int(remaining + 0.1):  # update ~every second
                self._update_overlay(f"📸 Screenshot in {remaining:.0f}s...")
        else:
            self._take_screenshot()

    def _take_screenshot(self):
        self._screenshot_taken = True
        save_dir = self._config.get("screenshot_dir", os.path.expanduser("~/Pictures"))
        os.makedirs(save_dir, exist_ok=True)
        from datetime import datetime
        fname    = f"ultron_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        save_path = os.path.join(save_dir, fname)
        # Prevent overwrite
        base, ext = os.path.splitext(save_path)
        counter = 1
        while os.path.exists(save_path):
            save_path = f"{base}_{counter}{ext}"
            counter += 1
        success = self._input.screenshot(save_path)
        if success:
            self._update_overlay(f"✅ Screenshot saved!")
            _speak_safe(f"Screenshot saved Sir.")
            _log(f"Screenshot saved: {save_path}")
        else:
            self._update_overlay("❌ Screenshot failed")
            _log("Screenshot failed", "error")

    # ─── Overlay ─────────────────────────────────────────────────

    def _init_overlay(self):
        try:
            from .hands_free_overlay import HandsFreeOverlay
            self._overlay = HandsFreeOverlay()
            self._overlay.show()
        except Exception as e:
            _log(f"Overlay init failed: {e}", "warning")

    def _update_overlay(self, msg: str):
        if self._overlay:
            try:
                self._overlay.update_status(msg, self._state.name)
            except Exception:
                pass

    def _close_overlay(self):
        if self._overlay:
            try:
                self._overlay.close_overlay()
            except Exception:
                pass
            self._overlay = None
