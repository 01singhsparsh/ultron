"""
copilot.py
AI Racing Co-Pilot for ULTRON Gaming Mode.
Intelligent, contextual voice feedback like an F1 race engineer.
Never spams. Only speaks when useful.
"""
import time
import threading
import random

class RacingCopilot:
    def __init__(self):
        self.last_spoken    = {}       # message_type -> last spoken time
        self.cooldowns      = {        # message_type -> cooldown seconds
            "tracking_lost":    4.0,
            "tracking_found":   3.0,
            "oversteer":        3.5,
            "understeer":       3.5,
            "nitro":            5.0,
            "brake_hard":       2.0,
            "accelerate":       6.0,
            "drift":            4.0,
            "perfect_steer":    5.0,
            "recovery":         4.0,
            "center":           6.0,
            "speed_warning":    5.0,
            "handbrake":        3.0,
        }
        self.prev_steering   = 0.0
        self.prev_speed      = 0
        self.steering_history= []
        self.nitro_available = True
        self.nitro_used_time = 0
        self.enabled         = True
        self._speak_queue    = []
        self._lock           = threading.Lock()

        # Start speak worker
        threading.Thread(target=self._speak_worker, daemon=True).start()

    def _can_speak(self, msg_type: str) -> bool:
        now      = time.time()
        last     = self.last_spoken.get(msg_type, 0)
        cooldown = self.cooldowns.get(msg_type, 3.0)
        return now - last > cooldown

    def _queue_speech(self, text: str, msg_type: str, priority: int = 1):
        """Queue a speech message with cooldown check."""
        if not self.enabled: return
        if not self._can_speak(msg_type): return
        self.last_spoken[msg_type] = time.time()
        with self._lock:
            # Remove lower priority messages of same type
            self._speak_queue = [m for m in self._speak_queue if m[2] != msg_type]
            self._speak_queue.append((text, priority, msg_type))
            # Sort by priority (higher = sooner)
            self._speak_queue.sort(key=lambda x: x[1], reverse=True)

    def _speak_worker(self):
        """Background thread that speaks queued messages."""
        while True:
            if self._speak_queue:
                with self._lock:
                    if self._speak_queue:
                        text, priority, msg_type = self._speak_queue.pop(0)
                    else:
                        text = None
                if text:
                    try:
                        from modules.speaker import speak
                        speak(text)
                    except:
                        print(f"[COPILOT] {text}")
            time.sleep(0.1)

    def analyze(self, status: dict, speed: int, hands_detected: bool):
        """
        Main analysis function — called every frame.
        Only speaks when something meaningful happens.
        """
        if not self.enabled: return

        steering    = status.get("steering", 0.0)
        keys        = status.get("keys_pressed", [])
        gesture     = status.get("action", "")
        is_braking  = "s" in keys
        is_accel    = "w" in keys
        is_nitro    = " " in keys or "nitro" in gesture.lower()
        is_handbrake= "shift" in keys

        # Track steering history
        self.steering_history.append(steering)
        if len(self.steering_history) > 30:
            self.steering_history = self.steering_history[-30:]

        # 1 — Tracking lost/found
        if not hands_detected:
            self._queue_speech("Tracking lost.", "tracking_lost", priority=5)
            return
        else:
            if self.last_spoken.get("tracking_lost",0) > 0:
                if time.time() - self.last_spoken.get("tracking_lost",0) < 6:
                    self._queue_speech("Hands detected.", "tracking_found", priority=4)

        # 2 — Oversteer warning
        if abs(steering) > 0.7:
            direction = "left" if steering < 0 else "right"
            self._queue_speech(f"Avoid oversteering {direction}.", "oversteer", priority=3)

        # 3 — Nitro available
        now = time.time()
        if is_nitro:
            self.nitro_available  = False
            self.nitro_used_time  = now
            self._queue_speech("Nitro!", "nitro", priority=4)
        elif now - self.nitro_used_time > 8:
            self.nitro_available = True

        # 4 — Hard brake detection
        speed_drop = self.prev_speed - speed
        if speed_drop > 15 and is_braking:
            self._queue_speech(random.choice([
                "Braking hard.",
                "Good brake.",
                "Hold it."
            ]), "brake_hard", priority=2)

        # 5 — Drift detection
        if abs(steering) > 0.5 and speed > 60 and is_accel:
            self._queue_speech(random.choice([
                "Excellent drift.",
                "Nice angle.",
                "Hold the drift."
            ]), "drift", priority=2)

        # 6 — Perfect steering
        if 0.05 < abs(steering) < 0.25 and is_accel and speed > 40:
            self._queue_speech(random.choice([
                "Perfect line.",
                "Smooth steering.",
                "Good control."
            ]), "perfect_steer", priority=1)

        # 7 — Handbrake
        if is_handbrake:
            self._queue_speech("Handbrake!", "handbrake", priority=3)

        # 8 — Acceleration
        if is_accel and speed < 20 and self.prev_speed < 5:
            self._queue_speech(random.choice([
                "Full throttle.",
                "Go go go!",
                "Accelerating."
            ]), "accelerate", priority=1)

        # 9 — Recovery
        if abs(self.prev_steering) > 0.6 and abs(steering) < 0.2:
            self._queue_speech(random.choice([
                "Good recovery.",
                "Back on track.",
                "Well corrected."
            ]), "recovery", priority=2)

        # 10 — Centering
        if abs(steering) < 0.05 and abs(self.prev_steering) > 0.3 and speed > 30:
            self._queue_speech("Centered.", "center", priority=1)

        self.prev_steering = steering
        self.prev_speed    = speed

    def announce(self, message: str):
        """Force an announcement regardless of cooldowns."""
        try:
            from modules.speaker import speak
            threading.Thread(target=speak, args=(message,), daemon=True).start()
        except:
            print(f"[COPILOT] {message}")

    def set_enabled(self, enabled: bool):
        self.enabled = enabled