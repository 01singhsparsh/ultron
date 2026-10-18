"""
hands_free/cursor_smoother.py
Smooth cursor position using exponential moving average.
Maps camera coordinates to screen coordinates.
"""


class CursorSmoother:
    def __init__(self,
                 smoothing:    float = 0.65,
                 dead_zone:    float = 0.02,
                 sensitivity:  float = 1.0,
                 mirrored:     bool  = True):
        self._alpha      = 1.0 - smoothing
        self._dead_zone  = dead_zone
        self._sensitivity = sensitivity
        self._mirrored   = mirrored
        self._sx: float  = 0.5
        self._sy: float  = 0.5
        self._initialized = False

    def update(self, cam_x: float, cam_y: float) -> tuple:
        """
        Feed camera-space coords (0-1), get smoothed screen-space coords (0-1).
        """
        if self._mirrored:
            cam_x = 1.0 - cam_x

        # Apply dead zone
        if not self._initialized:
            self._sx = cam_x
            self._sy = cam_y
            self._initialized = True
            return (cam_x, cam_y)

        dx = cam_x - self._sx
        dy = cam_y - self._sy

        if abs(dx) < self._dead_zone:
            dx = 0.0
        if abs(dy) < self._dead_zone:
            dy = 0.0

        # Sensitivity
        dx *= self._sensitivity
        dy *= self._sensitivity

        # EMA smoothing
        self._sx += self._alpha * dx
        self._sy += self._alpha * dy

        # Clamp
        self._sx = max(0.0, min(1.0, self._sx))
        self._sy = max(0.0, min(1.0, self._sy))

        return (self._sx, self._sy)

    def reset(self):
        self._initialized = False
