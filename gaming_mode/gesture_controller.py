"""
gesture_controller.py
Maps hand gestures to keyboard/game controls.
Works with any game that uses WASD or arrow keys.
"""
import time
import numpy as np

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE    = 0
except: pass

try:
    import pynput.keyboard as pynkey
    _keyboard = pynkey.Controller()
    USE_PYNPUT = True
except:
    USE_PYNPUT = False

# Key state tracking — avoid spamming key presses
_pressed_keys = set()

def _press(key):
    """Press and hold a key."""
    if key not in _pressed_keys:
        _pressed_keys.add(key)
        try:
            if USE_PYNPUT:
                _keyboard.press(key)
            else:
                pyautogui.keyDown(key)
        except: pass

def _release(key):
    """Release a key."""
    if key in _pressed_keys:
        _pressed_keys.discard(key)
        try:
            if USE_PYNPUT:
                _keyboard.release(key)
            else:
                pyautogui.keyUp(key)
        except: pass

def _tap(key):
    """Quick tap a key."""
    try:
        if USE_PYNPUT:
            _keyboard.press(key); time.sleep(0.05); _keyboard.release(key)
        else:
            pyautogui.press(key)
    except: pass

def release_all():
    """Release all currently pressed keys."""
    for key in list(_pressed_keys):
        _release(key)

class GestureController:
    def __init__(self):
        self.current_gestures  = set()
        self.prev_gestures     = set()
        self.steering_angle    = 0.0
        self.last_action       = ""
        self.action_history    = []
        self.enabled           = True

        # Gesture → action mapping
        self.GESTURE_MAP = {
            "fist":       self._accelerate,
            "open_palm":  self._brake,
            "point":      self._nitro,
            "pinch":      self._handbrake,
            "peace":      self._pause,
        }

        # Steering thresholds
        self.STEER_LEFT_THRESHOLD  = -0.15
        self.STEER_RIGHT_THRESHOLD =  0.15

    def _accelerate(self, active):
        """Fist = Accelerate (W key)"""
        if active:
            _press('w')
            self.last_action = "ACCELERATE ✊"
        else:
            _release('w')

    def _brake(self, active):
        """Open palm = Brake (S key)"""
        if active:
            _press('s')
            _release('w')
            self.last_action = "BRAKE ✋"
        else:
            _release('s')

    def _nitro(self, active):
        """Pointing = Nitro (Space)"""
        if active and "point" not in self.prev_gestures:
            _tap(' ')
            self.last_action = "NITRO ☝️"

    def _handbrake(self, active):
        """Pinch = Handbrake (Shift)"""
        if active:
            _press('shift')
            self.last_action = "HANDBRAKE 🤏"
        else:
            _release('shift')

    def _pause(self, active):
        """Peace sign = Pause (Escape)"""
        if active and "peace" not in self.prev_gestures:
            _tap('escape')
            self.last_action = "PAUSE ✌️"

    def _steer(self, angle):
        """
        Steer based on hand tilt angle.
        angle: float from -1.0 (full left) to +1.0 (full right)
        """
        if angle < self.STEER_LEFT_THRESHOLD:
            # Steer left
            _press('a')
            _release('d')
            # Proportional — harder tilt = hold longer
            intensity = min(abs(angle) * 3, 1.0)
            self.last_action = f"STEER LEFT {'◀'*int(intensity*3+1)}"
        elif angle > self.STEER_RIGHT_THRESHOLD:
            # Steer right
            _press('d')
            _release('a')
            intensity = min(abs(angle) * 3, 1.0)
            self.last_action = f"STEER RIGHT {'▶'*int(intensity*3+1)}"
        else:
            # Center — release steering
            _release('a')
            _release('d')
            if "STEER" in self.last_action:
                self.last_action = "CENTER —"

    def process(self, hands_data: list, recognized_gestures: list):
        """
        Main processing function.
        Called every frame with hand tracking data.
        """
        if not self.enabled or not hands_data:
            release_all()
            return

        self.prev_gestures = self.current_gestures.copy()
        self.current_gestures = set(g['name'] for g in recognized_gestures)

        # Process steering from hand orientation
        if hands_data:
            hand = hands_data[0]
            lm   = hand['landmarks']

            # Calculate steering angle from wrist and middle finger
            wrist  = lm[0]
            middle = lm[12]
            index  = lm[8]
            pinky  = lm[20]

            # Horizontal tilt of the hand
            hand_width = pinky['x'] - index['x']
            hand_height= lm[5]['y'] - lm[17]['y']

            # Steering = horizontal displacement of palm center
            palm_x     = (lm[5]['x'] + lm[17]['x']) / 2
            frame_cx   = 640  # Assume 1280 wide / 2

            # Normalize steering angle
            raw_angle  = (palm_x - frame_cx) / frame_cx
            # Smooth it
            self.steering_angle = self.steering_angle * 0.6 + raw_angle * 0.4
            self._steer(self.steering_angle)

        # Process gesture-based controls
        for gesture_name, handler in self.GESTURE_MAP.items():
            is_active = gesture_name in self.current_gestures
            handler(is_active)

        # Log action history
        if self.last_action:
            self.action_history.append(self.last_action)
            if len(self.action_history) > 10:
                self.action_history = self.action_history[-10:]

    def recognize_peace(self, hand_landmarks):
        """Detect peace/victory sign gesture."""
        lm = hand_landmarks
        try:
            index_up  = lm[8]['y']  < lm[6]['y']
            middle_up = lm[12]['y'] < lm[10]['y']
            ring_down = lm[16]['y'] > lm[14]['y']
            pinky_down= lm[20]['y'] > lm[18]['y']
            return index_up and middle_up and ring_down and pinky_down
        except:
            return False

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        if not enabled:
            release_all()

    def get_status(self) -> dict:
        return {
            "enabled":       self.enabled,
            "action":        self.last_action,
            "keys_pressed":  list(_pressed_keys),
            "steering":      round(self.steering_angle, 2),
            "gestures":      list(self.current_gestures),
        }