"""
hands_free/feature_extractor.py
Extracts normalized HandFeatures from raw MediaPipe landmark results.
"""
import time
import math
from typing import Optional, Any
from .hand_features import HandFeatures, FingerStates


def _dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _lm(landmarks, idx) -> tuple:
    lm = landmarks[idx]
    return (lm.x, lm.y)


def extract_features(mp_result: Any, mirrored: bool = True) -> Optional[HandFeatures]:
    """
    Extract HandFeatures from a MediaPipe Hands result.
    Returns None if no hand detected or landmarks missing.
    """
    try:
        if not mp_result.multi_hand_landmarks:
            return None

        landmarks = mp_result.multi_hand_landmarks[0]
        lms = landmarks.landmark

        # Handedness
        handedness = "Right"
        if mp_result.multi_handedness:
            label = mp_result.multi_handedness[0].classification[0].label
            handedness = label
            if mirrored:
                handedness = "Left" if label == "Right" else "Right"

        # Confidence
        confidence = 0.0
        if mp_result.multi_handedness:
            confidence = mp_result.multi_handedness[0].classification[0].score

        # Key positions (normalized 0-1)
        wrist     = _lm(lms, 0)
        thumb_tip = _lm(lms, 4)
        index_mcp = _lm(lms, 5)
        index_pip = _lm(lms, 6)
        index_tip = _lm(lms, 8)
        middle_tip = _lm(lms, 12)
        ring_tip   = _lm(lms, 16)
        pinky_tip  = _lm(lms, 20)
        pinky_mcp  = _lm(lms, 17)
        middle_mcp = _lm(lms, 9)

        # Palm center (average of wrist + MCP joints)
        palm_cx = (lms[0].x + lms[5].x + lms[9].x + lms[13].x + lms[17].x) / 5
        palm_cy = (lms[0].y + lms[5].y + lms[9].y + lms[13].y + lms[17].y) / 5
        palm_center = (palm_cx, palm_cy)

        # Hand size (distance wrist to middle_mcp)
        hand_size = _dist(wrist, middle_mcp)

        # Finger states (extended = tip above pip joint in y-axis)
        def finger_extended(tip_idx, pip_idx) -> bool:
            tip = lms[tip_idx].y
            pip = lms[pip_idx].y
            return tip < pip  # smaller y = higher on screen

        # Thumb: use x-axis comparison relative to handedness
        thumb_extended = abs(lms[4].x - lms[3].x) > 0.04

        finger_states = FingerStates(
            thumb  = thumb_extended,
            index  = finger_extended(8, 6),
            middle = finger_extended(12, 10),
            ring   = finger_extended(16, 14),
            pinky  = finger_extended(20, 18),
        )

        # Pinch distance (thumb tip to index tip, normalized by hand size)
        raw_pinch = _dist(thumb_tip, index_tip)
        pinch_distance = raw_pinch / max(hand_size, 0.001)

        # Palm orientation
        wrist_y  = lms[0].y
        middle_y = lms[12].y
        wrist_x  = lms[0].x
        middle_x = lms[12].x

        if abs(wrist_y - middle_y) > abs(wrist_x - middle_x):
            palm_orientation = "up" if wrist_y > middle_y else "down"
        else:
            palm_orientation = "right" if wrist_x < middle_x else "left"

        return HandFeatures(
            handedness       = handedness,
            confidence       = confidence,
            wrist_position   = wrist,
            palm_center      = palm_center,
            index_tip        = index_tip,
            thumb_tip        = thumb_tip,
            middle_tip       = middle_tip,
            ring_tip         = ring_tip,
            pinky_tip        = pinky_tip,
            finger_states    = finger_states,
            pinch_distance   = pinch_distance,
            palm_orientation = palm_orientation,
            hand_size        = hand_size,
            timestamp        = time.time(),
        )

    except Exception as e:
        return None
