"""
hands_free/hand_features.py
Normalized hand feature data structure extracted from MediaPipe landmarks.
"""
from dataclasses import dataclass, field
from typing import Optional, Tuple, List
import time

@dataclass
class FingerStates:
    thumb:  bool = False
    index:  bool = False
    middle: bool = False
    ring:   bool = False
    pinky:  bool = False

    @property
    def extended_count(self) -> int:
        return sum([self.thumb, self.index, self.middle, self.ring, self.pinky])

    def to_list(self) -> List[bool]:
        return [self.thumb, self.index, self.middle, self.ring, self.pinky]

@dataclass
class HandFeatures:
    """Normalized hand feature representation."""
    handedness:       str   = "Right"
    confidence:       float = 0.0
    wrist_position:   Tuple[float, float] = (0.0, 0.0)
    palm_center:      Tuple[float, float] = (0.0, 0.0)
    index_tip:        Tuple[float, float] = (0.0, 0.0)
    thumb_tip:        Tuple[float, float] = (0.0, 0.0)
    middle_tip:       Tuple[float, float] = (0.0, 0.0)
    ring_tip:         Tuple[float, float] = (0.0, 0.0)
    pinky_tip:        Tuple[float, float] = (0.0, 0.0)
    finger_states:    FingerStates = field(default_factory=FingerStates)
    pinch_distance:   float = 1.0   # normalized 0-1
    palm_orientation: str   = "unknown"  # up/down/left/right
    hand_size:        float = 0.0   # normalized palm size
    timestamp:        float = field(default_factory=time.time)

    def is_valid(self, min_confidence: float = 0.5) -> bool:
        return self.confidence >= min_confidence and self.hand_size > 0.0
