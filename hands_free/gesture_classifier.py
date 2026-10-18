from .hand_features import HandFeatures

class GestureClassifier:
    def __init__(self, config: dict = None):
        cfg = config or {}
        self.pinch_threshold = cfg.get("pinch_threshold", 0.25)
        self.min_confidence  = cfg.get("min_confidence",  0.55)

    def classify(self, features: HandFeatures) -> str:
        if not features or features.confidence < self.min_confidence:
            return "NONE"
        fs  = features.finger_states
        ext = fs.extended_count
        if ext == 0 and not fs.thumb:
            return "FIST"
        if features.pinch_distance < self.pinch_threshold and features.finger_states.thumb and features.finger_states.index:
            return "PINCH"
        if ext >= 4 and fs.index and fs.middle and fs.ring and fs.pinky:
            if fs.thumb:
                return "OPEN_PALM"
            return "FOUR_FINGER"
        if fs.index and fs.middle and fs.ring and fs.pinky and not fs.thumb:
            return "FOUR_FINGER"
        if fs.index and fs.middle and fs.ring and not fs.pinky and not fs.thumb:
            return "THREE_FINGER"
        if fs.index and fs.middle and not fs.ring and not fs.pinky:
            return "TWO_FINGER"
        if fs.thumb and ext == 1:
            wrist_y = features.wrist_position[1]
            thumb_y = features.thumb_tip[1]
            if thumb_y < wrist_y - 0.04:
                return "THUMBS_UP"
            elif thumb_y > wrist_y + 0.04:
                return "THUMBS_DOWN"
        if fs.pinky and not fs.index and not fs.middle and not fs.ring and ext <= 2:
            pinky_y = features.pinky_tip[1]
            wrist_y = features.wrist_position[1]
            return "PINKY_UP" if pinky_y < wrist_y else "PINKY_DOWN"
        if fs.index and not fs.middle and not fs.ring and not fs.pinky:
            return "INDEX_POINT"
        return "NONE"

