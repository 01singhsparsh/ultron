"""
Hands-Free Mode unit tests (no webcam required).
Run: py -3.11 -m pytest hands_free/tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import time
import pytest
from hands_free.hands_free_state   import HandsFreeState, can_transition
from hands_free.hand_features      import HandFeatures, FingerStates
from hands_free.gesture_classifier import GestureClassifier
from hands_free.gesture_stabilizer import GestureStabilizer
from hands_free.cursor_smoother    import CursorSmoother
from hands_free.voice_integration  import detect_hands_free_intent


# ── State machine tests ──────────────────────────────────────────

def test_valid_transition_inactive_to_starting():
    assert can_transition(HandsFreeState.INACTIVE, HandsFreeState.STARTING)

def test_invalid_transition_inactive_to_active():
    assert not can_transition(HandsFreeState.INACTIVE, HandsFreeState.ACTIVE)

def test_emergency_from_active():
    assert can_transition(HandsFreeState.ACTIVE, HandsFreeState.EMERGENCY_STOPPED)

def test_emergency_from_paused():
    assert can_transition(HandsFreeState.PAUSED, HandsFreeState.EMERGENCY_STOPPED)


# ── Gesture classifier tests ─────────────────────────────────────

def _make_features(**kwargs) -> HandFeatures:
    defaults = dict(
        confidence=0.9,
        wrist_position=(0.5, 0.8),
        thumb_tip=(0.4, 0.6),
        index_tip=(0.5, 0.3),
        middle_tip=(0.55, 0.4),
        ring_tip=(0.58, 0.45),
        pinky_tip=(0.6, 0.5),
        pinch_distance=0.6,
        finger_states=FingerStates(),
        hand_size=0.18,
    )
    defaults.update(kwargs)
    return HandFeatures(**defaults)

clf = GestureClassifier()

def test_classify_index_point():
    fs = FingerStates(index=True)
    f  = _make_features(finger_states=fs, pinch_distance=0.6)
    assert clf.classify(f) == "INDEX_POINT"

def test_classify_fist():
    fs = FingerStates(thumb=False)
    f  = _make_features(finger_states=fs, pinch_distance=0.6)
    assert clf.classify(f) == "FIST"

def test_classify_open_palm():
    fs = FingerStates(thumb=True, index=True, middle=True, ring=True, pinky=True)
    f  = _make_features(finger_states=fs, pinch_distance=0.6)
    assert clf.classify(f) == "OPEN_PALM"

def test_classify_pinch():
    fs = FingerStates(thumb=True, index=True)
    f  = _make_features(finger_states=fs, pinch_distance=0.2)
    assert clf.classify(f) == "PINCH"

def test_classify_two_finger():
    fs = FingerStates(index=True, middle=True)
    f  = _make_features(finger_states=fs, pinch_distance=0.6)
    assert clf.classify(f) == "TWO_FINGER"

def test_classify_three_finger():
    fs = FingerStates(index=True, middle=True, ring=True)
    f  = _make_features(finger_states=fs, pinch_distance=0.6)
    assert clf.classify(f) == "THREE_FINGER"

def test_classify_low_confidence_returns_none():
    fs = FingerStates(index=True)
    f  = _make_features(finger_states=fs, confidence=0.2)
    assert clf.classify(f) == "NONE"


# ── Stabilizer tests ─────────────────────────────────────────────

def test_stabilizer_requires_min_frames():
    stab   = GestureStabilizer(history_size=12)
    events = []
    stab.add_callback(events.append)
    # Feed fewer frames than min_frames (5 for PINCH)
    for _ in range(3):
        stab.update("PINCH", 0.9)
    assert len(events) == 0

def test_stabilizer_fires_after_enough_frames():
    stab   = GestureStabilizer(history_size=12)
    events = []
    stab.add_callback(events.append)
    # Feed enough stable OPEN_PALM frames (needs 8)
    for _ in range(20):
        stab.update("OPEN_PALM", 0.9)
        time.sleep(0.025)  # simulate ~40fps
    # Should have fired at least once
    assert any(e.gesture == "OPEN_PALM" for e in events)

def test_stabilizer_no_repeat_same_gesture():
    stab = GestureStabilizer(history_size=12)
    events = []
    stab.add_callback(events.append)
    for _ in range(30):
        stab.update("OPEN_PALM", 0.9)
        time.sleep(0.02)
    # Should not fire more than once (cooldown)
    palm_events = [e for e in events if e.gesture == "OPEN_PALM"]
    assert len(palm_events) <= 1


# ── Cursor smoother tests ────────────────────────────────────────

def test_smoother_mirrors():
    s = CursorSmoother(mirrored=True, dead_zone=0.0, smoothing=0.0)
    x, y = s.update(0.2, 0.5)
    # After first call just initializes
    x, y = s.update(0.2, 0.5)
    assert abs(x - 0.8) < 0.01  # mirrored

def test_smoother_dead_zone():
    s = CursorSmoother(mirrored=False, dead_zone=0.05, smoothing=0.0)
    s.update(0.5, 0.5)   # init
    x, y = s.update(0.52, 0.5)   # tiny move < dead zone
    assert abs(x - 0.5) < 0.01  # should not move

def test_smoother_clamps():
    s = CursorSmoother(mirrored=False, dead_zone=0.0, smoothing=0.0, sensitivity=3.0)
    s.update(0.5, 0.5)
    x, y = s.update(2.0, 2.0)
    assert x <= 1.0 and y <= 1.0


# ── Voice integration tests ──────────────────────────────────────

def test_detect_enable():
    r = detect_hands_free_intent("Ultron open hands free mode")
    assert r["matched"] and r["action"] == "enable"

def test_detect_enable_hinglish():
    r = detect_hands_free_intent("Ultron hand control on karo")
    assert r["matched"] and r["action"] == "enable"

def test_detect_disable():
    r = detect_hands_free_intent("Ultron stop hand control")
    assert r["matched"] and r["action"] == "disable"

def test_detect_emergency():
    r = detect_hands_free_intent("Ultron emergency stop")
    assert r["matched"] and r["action"] == "emergency_stop"

def test_detect_no_match():
    r = detect_hands_free_intent("play some music please")
    assert not r["matched"]

def test_detect_calibrate():
    r = detect_hands_free_intent("Ultron calibrate hands free mode")
    assert r["matched"] and r["action"] == "calibrate"
