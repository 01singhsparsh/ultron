
MEDIA_KEYWORDS = {
    "play":              ("media","play"),
    "pause":             ("media","pause"),
    "play pause":        ("media","playpause"),
    "stop music":        ("media","stop"),
    "next song":         ("media","next"),
    "next track":        ("media","next"),
    "previous song":     ("media","prev"),
    "previous track":    ("media","prev"),
    "skip forward":      ("media","forward10"),
    "skip 10":           ("media","forward10"),
    "forward 10":        ("media","forward10"),
    "skip backward":     ("media","back10"),
    "back 10":           ("media","back10"),
    "rewind 10":         ("media","back10"),
    "go back 10":        ("media","back10"),
    "mute":              ("media","mute"),
    "unmute":            ("media","mute"),
    "full screen":       ("media","fullscreen"),
    "fullscreen":        ("media","fullscreen"),
    "volume up":         ("media","volup"),
    "volume down":       ("media","voldown"),
}
ACTIVATE_KEYWORDS = [
    "hands free mode","hands-free mode","hand free mode",
    "handsfree mode","handsfree","hands free",
    "hand control on","gesture mode on","gesture mode start",
    "haath se control","hands free chalu","hand control chalu",
    "gesture control on","open hands free","open handsfree",
    "start hands free","start handsfree","activate gesture",
    "enable gesture mode","webcam control","open hand free",
    "hand free mode","gesture mode","hand mode",
]
DEACTIVATE_KEYWORDS = [
    "stop hand control","hands free off","close hands free",
    "disable gesture","gesture mode off","hand mode stop",
    "hand control off","stop gesture","disable hands free",
    "stop handsfree","handsfree off","close handsfree",
    "stop hand free","hand free off",
]
EMERGENCY_KEYWORDS = ["emergency stop","emergency","stop everything"]
PAUSE_KEYWORDS     = ["pause hands free","pause gesture","lock hands free"]
RESUME_KEYWORDS    = ["resume hands free","resume gesture","unlock hands free"]
CALIBRATE_KEYWORDS = ["calibrate hands free","calibrate gesture"]
STATUS_KEYWORDS    = ["hands free status","gesture status"]

def detect_hands_free_intent(text: str) -> dict:
    t = text.lower().strip()
    for kw in EMERGENCY_KEYWORDS:
        if kw in t:
            return {"matched": True, "action": "emergency_stop"}
    for prefix in ["type ","likhna ","likho ","write ","search for ","search "]:
        if t.startswith(prefix):
            typed_text = text[len(prefix):].strip()
            if typed_text:
                return {"matched": True, "action": "type_text", "text": typed_text}
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
    if any(kw in t for kw in ["show desktop","go to desktop","swipe to desktop"]):
        return {"matched": True, "action": "show_desktop"}
    # Media voice commands
    for kw, action in MEDIA_KEYWORDS.items():
        if kw in t:
            return {"matched": True, "action": "media", "cmd": action[1]}
    # Voice click command
    if t in ['click','left click','click here','do click','press click','kar click','click karo']:
        return {'matched': True, 'action': 'voice_click'}

    # Voice click command
    if t in ['click','left click','click here','do click','press click','kar click','click karo']:
        return {'matched': True, 'action': 'voice_click'}

    for kw in ACTIVATE_KEYWORDS:
        if kw in t:
            return {"matched": True, "action": "enable"}
    return {"matched": False, "action": None}

def handle_hands_free_command(text: str) -> bool:
    result = detect_hands_free_intent(text)
    if not result["matched"]:
        return False
    from .hands_free_manager import HandsFreeManager
    mgr    = HandsFreeManager.get_instance()
    action = result["action"]
    if action == "enable":           mgr.enable()
    elif action == "disable":        mgr.disable("voice command")
    elif action == "emergency_stop": mgr.emergency_stop()
    elif action == "pause":          mgr.pause()
    elif action == "resume":         mgr.resume()
    elif action == "calibrate":      mgr.calibrate()
    elif action == "show_desktop":   mgr.show_desktop()
    elif action == "type_text":      mgr.type_text(result.get("text",""))
    elif action == "status":
        try:
            from modules.speaker import speak
            speak(f"Hands-Free Mode is {mgr.status()} Sir.")
        except Exception: pass
    return True





