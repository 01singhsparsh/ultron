"""
holographic_wheel.py
Holographic steering wheel that appears between the user's hands.
Follows hand movement, rotates with steering, glows with state.
Inspired by Tony Stark's holographic interfaces.
"""
import cv2
import numpy as np
import math
import time

class HolographicWheel:
    def __init__(self, width=1280, height=720):
        self.w           = width
        self.h           = height
        self.t           = 0.0

        # Wheel position — smoothed
        self.wheel_x     = width  // 2
        self.wheel_y     = height // 2
        self.wheel_r     = 100
        self.smooth_x    = float(width  // 2)
        self.smooth_y    = float(height // 2)
        self.smooth_r    = 100.0
        self.alpha       = 1.0       # Transparency 0-1
        self.target_alpha= 1.0

        # Rotation
        self.rotation    = 0.0
        self.smooth_rot  = 0.0

        # State
        self.state       = "idle"   # idle|accelerate|brake|nitro|drift
        self.state_time  = 0.0
        self.particles   = []

        # Colors (BGR)
        self.CYAN        = (230, 210, 0)
        self.GREEN       = (50,  230, 50)
        self.RED         = (30,  30,  230)
        self.BLUE        = (255, 100, 0)
        self.WHITE       = (255, 255, 255)
        self.ORANGE      = (30,  160, 255)

        # Smoothing
        self.SMOOTH      = 0.25     # Lower = smoother but more lag

    def _get_wheel_color(self):
        """Get wheel color based on current state."""
        now = time.time()
        age = now - self.state_time

        if self.state == "accelerate" and age < 0.5:
            t = age / 0.5
            r = int(self.CYAN[0] * t + self.GREEN[0] * (1-t))
            g = int(self.CYAN[1] * t + self.GREEN[1] * (1-t))
            b = int(self.CYAN[2] * t + self.GREEN[2] * (1-t))
            return (r, g, b)
        elif self.state == "brake" and age < 0.4:
            t = age / 0.4
            return (int(self.RED[0]*(1-t)+self.CYAN[0]*t),
                    int(self.RED[1]*(1-t)+self.CYAN[1]*t),
                    int(self.RED[2]*(1-t)+self.CYAN[2]*t))
        elif self.state == "nitro" and age < 0.8:
            pulse = abs(math.sin(age * 15))
            return (int(255*pulse), int(100*pulse), int(50*pulse))
        else:
            # Default cyan with slight pulse
            pulse = 0.85 + 0.15 * math.sin(self.t * 3)
            return (int(self.CYAN[0]*pulse), int(self.CYAN[1]*pulse), int(self.CYAN[2]*pulse))

    def _spawn_particles(self, cx, cy, count=8, color=None):
        """Spawn energy particles from wheel center."""
        if color is None: color = self.CYAN
        for _ in range(count):
            angle  = np.random.uniform(0, 2*math.pi)
            speed  = np.random.uniform(2, 8)
            life   = np.random.uniform(0.3, 0.8)
            self.particles.append({
                "x":     float(cx), "y": float(cy),
                "vx":    math.cos(angle) * speed,
                "vy":    math.sin(angle) * speed,
                "life":  life, "max_life": life,
                "color": color, "size": np.random.randint(2,5)
            })

    def _update_particles(self, frame):
        """Update and draw energy particles."""
        alive = []
        for p in self.particles:
            p["life"] -= 0.033
            if p["life"] <= 0: continue
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vx"] *= 0.92
            p["vy"] *= 0.92
            alpha_ratio = p["life"] / p["max_life"]
            color = tuple(int(c * alpha_ratio) for c in p["color"])
            cx, cy = int(p["x"]), int(p["y"])
            if 0 < cx < self.w and 0 < cy < self.h:
                cv2.circle(frame, (cx,cy), p["size"], color, -1)
            alive.append(p)
        self.particles = alive

    def _draw_glow_circle(self, frame, cx, cy, r, color, thickness=2, glow_layers=4):
        """Draw a circle with glow effect."""
        overlay = frame.copy()
        for i in range(glow_layers, 0, -1):
            glow_r = r + i * 3
            alpha  = 0.15 * (glow_layers - i + 1) / glow_layers
            c      = tuple(int(ch * alpha) for ch in color)
            cv2.circle(overlay, (cx,cy), glow_r, c, thickness + i)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        cv2.circle(frame, (cx,cy), r, color, thickness)

    def _draw_wheel(self, frame, cx, cy, r, rotation_deg, color, state_alpha):
        """Draw the holographic steering wheel."""
        cx, cy, r = int(cx), int(cy), int(r)

        # ── Outer glow ring (rotates) ──
        for i in range(0, 360, 6):
            angle  = math.radians(i + rotation_deg * 2)
            px     = int(cx + (r+12) * math.cos(angle))
            py     = int(cy + (r+12) * math.sin(angle))
            bright = abs(math.sin(math.radians(i + self.t * 60)))
            c      = tuple(int(ch * bright * state_alpha) for ch in color)
            if 0 < px < self.w and 0 < py < self.h:
                cv2.circle(frame, (px,py), 2, c, -1)

        # ── Main wheel ring ──
        self._draw_glow_circle(frame, cx, cy, r, color, thickness=3, glow_layers=5)

        # ── Inner ring ──
        self._draw_glow_circle(frame, cx, cy, r-12, color, thickness=1, glow_layers=2)

        # ── 3 Spokes ──
        for i in range(3):
            spoke_angle = math.radians(rotation_deg + i * 120)
            x1 = int(cx + 18  * math.cos(spoke_angle))
            y1 = int(cy + 18  * math.sin(spoke_angle))
            x2 = int(cx + (r-8) * math.cos(spoke_angle))
            y2 = int(cy + (r-8) * math.sin(spoke_angle))
            cv2.line(frame, (x1,y1), (x2,y2), color, 3)
            # Spoke glow
            overlay = frame.copy()
            cv2.line(overlay, (x1,y1), (x2,y2), color, 7)
            cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)

        # ── Grip areas on rim ──
        for i in range(6):
            grip_angle = math.radians(rotation_deg + i * 60 + 30)
            gx = int(cx + r * math.cos(grip_angle))
            gy = int(cy + r * math.sin(grip_angle))
            self._draw_glow_circle(frame, gx, gy, 7, color, thickness=-1, glow_layers=2)

        # ── Pulsating center core ──
        core_pulse = 0.7 + 0.3 * math.sin(self.t * 6)
        core_r     = int(16 * core_pulse)
        core_color = tuple(int(ch * core_pulse) for ch in color)
        cv2.circle(frame, (cx,cy), core_r+6, tuple(int(c*0.3) for c in color), -1)
        cv2.circle(frame, (cx,cy), core_r,   core_color, -1)
        cv2.circle(frame, (cx,cy), 6,         self.WHITE, -1)

        # ── Energy ring (animated) ──
        energy_angle = self.t * 150 % 360
        for d in range(0, 60, 10):
            a  = math.radians(energy_angle + d)
            ex = int(cx + (r-4) * math.cos(a))
            ey = int(cy + (r-4) * math.sin(a))
            if 0 < ex < self.w and 0 < ey < self.h:
                brightness = 1.0 - d/60
                c = tuple(int(ch * brightness) for ch in color)
                cv2.circle(frame, (ex,ey), 3, c, -1)

    def _draw_state_effect(self, frame, cx, cy, r):
        """Draw state-specific visual effects."""
        now = time.time()
        age = now - self.state_time

        if self.state == "nitro" and age < 1.0:
            # Blue energy waves radiating outward
            wave_r = int(r + age * 150)
            alpha  = max(0, 1.0 - age)
            overlay = frame.copy()
            cv2.circle(overlay, (cx,cy), wave_r, self.BLUE, 3)
            cv2.circle(overlay, (cx,cy), wave_r+15, self.BLUE, 1)
            cv2.addWeighted(overlay, alpha * 0.6, frame, 1-alpha*0.6, 0, frame)

        elif self.state == "accelerate" and age < 0.3:
            # Green pulse
            overlay = frame.copy()
            cv2.circle(overlay, (cx,cy), r+20, self.GREEN, 4)
            cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

        elif self.state == "brake" and age < 0.3:
            # Red flash
            overlay = frame.copy()
            cv2.rectangle(overlay, (0,0), (self.w, self.h), self.RED, -1)
            cv2.addWeighted(overlay, 0.08, frame, 0.92, 0, frame)

    def _draw_mini_hud(self, frame, speed, steering, state):
        """Draw minimal transparent HUD — speed and state only."""
        # Top-right speed display
        overlay = frame.copy()
        cv2.rectangle(overlay, (self.w-140, 45), (self.w-10, 100), (0,0,0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        cv2.putText(frame, f"{speed}", (self.w-110, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.4, self.CYAN, 2)
        cv2.putText(frame, "KM/H", (self.w-100, 108),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, self.CYAN, 1)

        # Steering bar — subtle at bottom center
        bar_w  = 200
        bar_cx = self.w // 2
        bar_y  = self.h - 20
        cv2.line(frame, (bar_cx-bar_w//2, bar_y), (bar_cx+bar_w//2, bar_y), (60,60,60), 2)
        steer_x = int(bar_cx + steering * bar_w//2)
        steer_x = max(bar_cx-bar_w//2, min(bar_cx+bar_w//2, steer_x))
        cv2.circle(frame, (steer_x, bar_y), 6, self.CYAN, -1)
        cv2.circle(frame, (bar_cx,  bar_y), 3, (100,100,100), -1)

    def update_state(self, keys_pressed: list, gesture: str):
        """Update visual state based on controls."""
        if " " in keys_pressed or "nitro" in gesture.lower():
            if self.state != "nitro":
                self.state      = "nitro"
                self.state_time = time.time()
                self._spawn_particles(int(self.smooth_x), int(self.smooth_y),
                                     count=20, color=self.BLUE)
        elif "w" in keys_pressed:
            if self.state != "accelerate":
                self.state      = "accelerate"
                self.state_time = time.time()
                self._spawn_particles(int(self.smooth_x), int(self.smooth_y),
                                     count=8, color=self.GREEN)
        elif "s" in keys_pressed:
            if self.state != "brake":
                self.state      = "brake"
                self.state_time = time.time()
        else:
            if self.state not in ["idle", "drift"]:
                self.state      = "idle"
                self.state_time = time.time()

    def render(self, frame, hands_data: list, steering_angle: float,
               speed: int, status: dict) -> np.ndarray:
        """
        Main render function.
        Positions wheel between hands, rotates with steering.
        """
        self.t += 0.033

        keys_pressed = status.get("keys_pressed", [])
        gesture      = status.get("action", "")

        # Update state
        self.update_state(keys_pressed, gesture)

        # Find wheel position from hands
        if len(hands_data) >= 2:
            # Two hands — position between them
            h1  = hands_data[0]
            h2  = hands_data[1]
            cx  = (h1['palm'][0] + h2['palm'][0]) / 2
            cy  = (h1['palm'][1] + h2['palm'][1]) / 2
            # Scale based on hand distance
            dist     = math.sqrt((h1['palm'][0]-h2['palm'][0])**2 + (h1['palm'][1]-h2['palm'][1])**2)
            target_r = max(60, min(160, dist * 0.45))
            self.target_alpha = 1.0

        elif len(hands_data) == 1:
            # One hand — center on palm
            h   = hands_data[0]
            cx  = h['palm'][0]
            cy  = h['palm'][1]
            target_r = 90
            self.target_alpha = 0.7

        else:
            # No hands — fade out
            cx       = self.smooth_x
            cy       = self.smooth_y
            target_r = self.smooth_r
            self.target_alpha = max(0, self.target_alpha - 0.05)

        # Smooth position
        s = self.SMOOTH
        self.smooth_x = self.smooth_x * (1-s) + cx * s
        self.smooth_y = self.smooth_y * (1-s) + cy * s
        self.smooth_r = self.smooth_r * (1-s) + target_r * s
        self.alpha    = self.alpha * 0.9 + self.target_alpha * 0.1

        if self.alpha < 0.05:
            self._draw_mini_hud(frame, speed, steering_angle, self.state)
            return frame

        # Smooth rotation
        target_rot   = steering_angle * 45
        self.smooth_rot = self.smooth_rot * 0.8 + target_rot * 0.2

        icx = int(self.smooth_x)
        icy = int(self.smooth_y)
        ir  = int(self.smooth_r)

        # Get current color
        color = self._get_wheel_color()

        # Apply transparency to wheel overlay
        wheel_overlay = frame.copy()

        # Draw state effects
        self._draw_state_effect(wheel_overlay, icx, icy, ir)

        # Draw main wheel
        self._draw_wheel(wheel_overlay, icx, icy, ir, self.smooth_rot, color, self.alpha)

        # Blend with alpha
        cv2.addWeighted(wheel_overlay, self.alpha, frame, 1-self.alpha*0.3, 0, frame)

        # Update and draw particles
        self._update_particles(frame)

        # Draw minimal HUD
        self._draw_mini_hud(frame, speed, steering_angle, self.state)

        return frame