class CursorSmoother:
    def __init__(self, smoothing=0.68, dead_zone=0.008, sensitivity=1.5, mirrored=True):
        self._alpha     = 1.0 - smoothing
        self._dead_zone = dead_zone
        self._sens      = sensitivity
        self._mirrored  = mirrored
        self._sx        = 0.5
        self._sy        = 0.5
        self._init      = False

    def update(self, cam_x: float, cam_y: float) -> tuple:
        if self._mirrored:
            cam_x = 1.0 - cam_x
        if not self._init:
            self._sx = cam_x
            self._sy = cam_y
            self._init = True
            return (cam_x, cam_y)
        dx = cam_x - self._sx
        dy = cam_y - self._sy
        if abs(dx) < self._dead_zone: dx = 0.0
        if abs(dy) < self._dead_zone: dy = 0.0
        boost = 1.4 if abs(dx) > 0.05 or abs(dy) > 0.05 else 1.0
        dx *= self._sens * boost
        dy *= self._sens * boost
        self._sx += self._alpha * dx
        self._sy += self._alpha * dy
        self._sx = max(0.02, min(0.98, self._sx))
        self._sy = max(0.02, min(0.98, self._sy))
        return (self._sx, self._sy)

    def reset(self):
        self._init = False
