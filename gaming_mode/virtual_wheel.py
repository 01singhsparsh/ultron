"""
virtual_wheel.py
Draws a holographic virtual steering wheel on the camera feed.
Shows current gesture, action, speed indicator, and controls.
"""
import cv2
import numpy as np
import math
import time

class VirtualWheel:
    def __init__(self, width=1280, height=720):
        self.w         = width
        self.h         = height
        self.angle     = 0.0
        self.speed     = 0
        self.max_speed = 100
        self.t         = 0.0

        # Colors (BGR)
        self.CYAN    = (230, 210, 0)
        self.GREEN   = (50,  230, 50)
        self.RED     = (50,  50,  230)
        self.ORANGE  = (30,  160, 255)
        self.WHITE   = (255, 255, 255)
        self.YELLOW  = (0,   230, 230)

    def _draw_steering_wheel(self, frame, cx, cy, radius, angle_deg):
        """Draw a steering wheel that rotates based on hand tilt."""
        # Outer ring
        cv2.circle(frame, (cx, cy), radius, self.CYAN, 3)
        cv2.circle(frame, (cx, cy), radius-8, self.CYAN, 1)

        # Center hub
        cv2.circle(frame, (cx, cy), 12, self.CYAN, -1)

        # Spokes (3 spokes, rotated)
        for i in range(3):
            spoke_angle = math.radians(angle_deg + i * 120)
            x1 = int(cx + 12  * math.cos(spoke_angle))
            y1 = int(cy + 12  * math.sin(spoke_angle))
            x2 = int(cx + (radius-5) * math.cos(spoke_angle))
            y2 = int(cy + (radius-5) * math.sin(spoke_angle))
            cv2.line(frame, (x1,y1), (x2,y2), self.CYAN, 3)

        # Grip areas on wheel
        for i in range(6):
            grip_angle = math.radians(angle_deg + i * 60 + 30)
            gx = int(cx + radius * math.cos(grip_angle))
            gy = int(cy + radius * math.sin(grip_angle))
            cv2.circle(frame, (gx, gy), 6, self.CYAN, -1)

    def _draw_speedometer(self, frame, cx, cy, radius):
        """Draw a speed gauge."""
        # Background arc
        for deg in range(220, 360+140, 2):
            rad = math.radians(deg)
            x   = int(cx + radius * math.cos(rad))
            y   = int(cy + radius * math.sin(rad))
            cv2.circle(frame, (x,y), 2, (50,50,50), -1)

        # Speed arc (filled based on current speed)
        speed_range = int(self.speed / self.max_speed * 280)
        color = self.GREEN
        if self.speed > 60: color = self.ORANGE
        if self.speed > 80: color = self.RED

        for deg in range(220, 220 + speed_range, 2):
            rad = math.radians(deg)
            x   = int(cx + radius * math.cos(rad))
            y   = int(cy + radius * math.sin(rad))
            cv2.circle(frame, (x,y), 3, color, -1)

        # Speed text
        cv2.putText(frame, f"{self.speed}", (cx-20, cy+10),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, self.WHITE, 2)
        cv2.putText(frame, "KM/H", (cx-22, cy+30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, self.CYAN, 1)

    def _draw_action_display(self, frame, action, status):
        """Draw current action and key status."""
        # Action box
        overlay = frame.copy()
        cv2.rectangle(overlay, (self.w-300, self.h-120), (self.w-10, self.h-10), (0,0,0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        cv2.rectangle(frame, (self.w-300, self.h-120), (self.w-10, self.h-10), self.CYAN, 2)

        cv2.putText(frame, "ACTION:", (self.w-285, self.h-95),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.CYAN, 1)
        cv2.putText(frame, action[:25] if action else "READY",
                   (self.w-285, self.h-70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.YELLOW, 2)

        # Keys pressed
        keys = status.get("keys_pressed", [])
        keys_str = " + ".join([k.upper() for k in keys]) if keys else "—"
        cv2.putText(frame, f"KEYS: {keys_str}", (self.w-285, self.h-40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.GREEN, 1)

        # Steering indicator
        steer = status.get("steering", 0)
        cv2.putText(frame, f"STEER: {steer:+.2f}", (self.w-285, self.h-20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.CYAN, 1)

    def _draw_gesture_guide(self, frame):
        """Draw gesture control guide."""
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, self.h-220), (220, self.h-10), (0,0,0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        cv2.rectangle(frame, (10, self.h-220), (220, self.h-10), self.CYAN, 1)

        cv2.putText(frame, "GESTURE CONTROLS", (15, self.h-200),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.CYAN, 1)

        guide = [
            "✊ Fist      → Accelerate",
            "✋ Palm      → Brake",
            "☝️ Point     → Nitro",
            "🤏 Pinch     → Handbrake",
            "↔️ Tilt      → Steer",
            "✌️ Peace     → Pause",
            "  Tilt Left  → Turn Left",
            "  Tilt Right → Turn Right",
        ]
        for i, line in enumerate(guide):
            cv2.putText(frame, line, (15, self.h-175 + i*23),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, self.WHITE, 1)

    def _draw_hud(self, frame, gesture_name):
        """Draw top HUD bar."""
        cv2.rectangle(frame, (0,0), (self.w,40), (20,10,0), -1)
        t_str = time.strftime("%H:%M:%S")
        cv2.putText(frame, f"ULTRON GAMING MODE  |  {t_str}  |  Press Q to exit",
                   (10,28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.CYAN, 1)

        # Gesture indicator
        if gesture_name:
            cv2.putText(frame, f"GESTURE: {gesture_name.upper()}",
                       (self.w-280, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.YELLOW, 1)

    def update(self, frame, steering_angle, speed, action, status, gesture_name=""):
        """Main render function."""
        self.t      += 0.05
        self.angle  = steering_angle * 45  # Max 45 degree wheel rotation
        self.speed  = min(max(speed, 0), self.max_speed)

        # Draw HUD
        self._draw_hud(frame, gesture_name)

        # Draw steering wheel — bottom right area
        wheel_cx = self.w - 120
        wheel_cy = self.h - 200
        wheel_r  = 80
        self._draw_steering_wheel(frame, wheel_cx, wheel_cy, wheel_r, self.angle)

        # Draw speedometer inside wheel area
        self._draw_speedometer(frame, wheel_cx, wheel_cy, 55)

        # Draw action display
        self._draw_action_display(frame, action, status)

        # Draw gesture guide
        self._draw_gesture_guide(frame)

        # Steering indicator bar (center bottom)
        bar_cx = self.w // 2
        bar_y  = self.h - 50
        bar_w  = 300

        # Background bar
        cv2.rectangle(frame, (bar_cx-bar_w//2, bar_y-8), (bar_cx+bar_w//2, bar_y+8), (50,50,50), -1)

        # Steering position
        steer_x = int(bar_cx + steering_angle * bar_w//2)
        steer_x = max(bar_cx-bar_w//2, min(bar_cx+bar_w//2, steer_x))
        cv2.rectangle(frame, (steer_x-10, bar_y-12), (steer_x+10, bar_y+12), self.YELLOW, -1)
        cv2.line(frame, (bar_cx, bar_y-15), (bar_cx, bar_y+15), self.CYAN, 2)

        # Labels
        cv2.putText(frame, "◀ LEFT", (bar_cx-bar_w//2, bar_y-18),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, self.CYAN, 1)
        cv2.putText(frame, "RIGHT ▶", (bar_cx+bar_w//2-65, bar_y-18),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, self.CYAN, 1)

        return frame