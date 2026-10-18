"""
hands_free/gesture_classifier.py
Classifies raw HandFeatures into named gesture labels.
"""
from typing import Optional
from .hand_features import HandFeatures


class GestureClassifier:
    """
    Classifies a HandFeatures snapshot into a gesture string.
    All thresholds are configurable.
    """

    GESTURES = [
        "NONE",
        "INDEX_POINT",      # cursor movement
        "PINCH",            # left click
        "TWO_FINGER",       # right click
        "OPEN_PALM",        # media play/pause
        "FIST",             # media/pause
        "THUMBS_UP",        # volume up
        "THUMBS_DOWN",      # volume down
        "PINKY_UP",         # scroll up
        "PINKY_DOWN",       # scroll down
        "THREE_FINGER",     # screenshot hold
    ]

    def __init__(self, config: dict = None):
        cfg = config or {}
        self.pinch_threshold   = cfg.get("pinch_threshold",   0.35)
        self.min_confidence    = cfg.get("min_confidence",    0.6)

    def classify(self, features: HandFeatures) -> str:
        if not features or features.confidence < self.min_confidence:
            return "NONE"

        fs = features.finger_states
        ext = fs.extended_count

        # FIST — all fingers folded
        if ext == 0 and not fs.thumb:
            return "FIST"

        # PINCH — thumb + index close, others folded
        if features.pinch_distance < self.pinch_threshold:
            return "PINCH"

        # OPEN_PALM — all 5 extended
        if ext >= 4 and fs.index and fs.middle and fs.ring and fs.pinky:
            return "OPEN_PALM"

        # THREE_FINGER — exactly index + middle + ring
        if fs.index and fs.middle and fs.ring and not fs.pinky and not fs.thumb:
            return "THREE_FINGER"

        # TWO_FINGER — index + middle only
        if fs.index and fs.middle and not fs.ring and not fs.pinky:
            return "TWO_FINGER"

        # THUMBS_UP — only thumb extended, pointing upward
        if fs.thumb and ext == 1:
            wrist_y = features.wrist_position[1]
            thumb_y = features.thumb_tip[1]
            if thumb_y < wrist_y - 0.05:
                return "THUMBS_UP"
            elif thumb_y > wrist_y + 0.05:
                return "THUMBS_DOWN"

        # PINKY_UP — only pinky extended
        if fs.pinky and not fs.index and not fs.middle and not fs.ring and ext <= 2:
            pinky_y = features.pinky_tip[1]
            wrist_y = features.wrist_position[1]
            if pinky_y < wrist_y:
                return "PINKY_UP"
            else:
                return "PINKY_DOWN"

        # INDEX_POINT — only index extended (cursor control)
        if fs.index and not fs.middle and not fs.ring and not fs.pinky:
            return "INDEX_POINT"

        return "NONE"
