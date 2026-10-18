"""
hands_free/voice_integration.py
Detects Hands-Free Mode voice commands and routes them.
Call handle_hands_free_command(text) from ultron.py command pipeline.
"""

ACTIVATE_KEYWORDS = [
    "hands free mode", "hands-free mode", "hand free mode",
    "hand control on", "gesture mode on", "gesture mode start",
    "haath se control", "hands free chalu", "hand control chalu",
    "haath se computer", "gesture control on", "open hands free",
    "start hands free", "activate gesture", "enable gesture mode",
    "webcam control", "camera control on",
]

DEACTIVATE_KEYWORDS = [
    "stop hand control", "hands free off", "close hands free",
    "disable gesture", "gesture mode off", "hand mode stop",
    "camera control band", "hand control off", "stop gesture",
    "disable hands free", "close gesture mode",
]

EMERGENCY_KEYWORDS = [
    "emergency stop", "emergency", "ultron stop everything",
]

PAUSE_KEYWORDS   = ["pause hands free", "pause gesture", "lock hands free"]
RESUME_KEYWORDS  = ["resume hands free", "resume gesture", "unlock hands free"]
CALIBRATE_KEYWORDS = ["calibrate hands free", "calibrate gesture", "calibrate camera"]
STATUS_KEYWORDS  = ["hands free status", "gesture status"]


def detect_hands_free_intent(text: str) -> dict:
    """
    Returns dict with keys: matched (bool), action (str)
    Actions: enable / disable / emergency_stop / pause / resume / calibrate / status
    """
    t = text.lower()

    for kw in EMERGENCY_KEYWORDS:
        if kw in t:
            return {"matched": True, "action": "emergency_stop"}

    for kw in DEACTIVATE_KEYWORDS:
        if kw in t:
            return {"matched": True, "action": "disable"}

    for kw in PAUSE_KEYWORDS:
        if kw in t:
            return {"matched": True, "action": "pause"}

    for kw in RESUME_KEYWORDS:
        if kw in t:
            return {"matched": True, "action": "resume"}

    for kw in CALIBRATE_KEYWORDS:
        if kw in t:
            return {"matched": True, "action": "calibrate"}

    for kw in STATUS_KEYWORDS:
        if kw in t:
            return {"matched": True, "action": "status"}

    for kw in ACTIVATE_KEYWORDS:
        if kw in t:
            return {"matched": True, "action": "enable"}

    return {"matched": False, "action": None}


def handle_hands_free_command(text: str) -> bool:
    """
    Call this from the main voice pipeline.
    Returns True if command was handled (skip other processing).
    """
    result = detect_hands_free_intent(text)
    if not result["matched"]:
        return False

    from .hands_free_manager import HandsFreeManager
    mgr = HandsFreeManager.get_instance()
    action = result["action"]

    if action == "enable":
        mgr.enable()
    elif action == "disable":
        mgr.disable("voice command")
    elif action == "emergency_stop":
        mgr.emergency_stop()
    elif action == "pause":
        mgr.pause()
    elif action == "resume":
        mgr.resume()
    elif action == "calibrate":
        mgr.calibrate()
    elif action == "status":
        try:
            from modules.speaker import speak
            speak(f"Hands-Free Mode is currently {mgr.status()} Sir.")
        except Exception:
            pass

    return True
