"""
smart_assistant.py
ULTRON Smart Awareness — Fixed version.
No false notifications. Suggestions only every 5 minutes max.
"""
import os, sys, time, threading, re, subprocess
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

GROQ_API_KEY  = ""
_running      = False
_notif_history= set()
_last_suggest = 0
_last_app     = ""
_last_wa_count= 0

# ── How often suggestions appear (seconds) ──
SUGGESTION_COOLDOWN = 300  # 5 minutes between suggestions

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def _speak(text):
    try:
        from modules.speaker import speak
        speak(text)
    except: print(f"[SMART] {text}")

def _listen(timeout=5):
    try:
        from modules.listener import listen
        return listen(timeout=timeout, phrase_limit=8)
    except: return None

def _get_wa_count() -> int:
    try:
        import pygetwindow as gw
        for win in gw.getAllWindows():
            if "whatsapp" in win.title.lower():
                m = re.search(r'\((\d+)\)', win.title)
                if m: return int(m.group(1))
    except: pass
    return 0

def _get_active_window() -> str:
    try:
        import pygetwindow as gw
        win = gw.getActiveWindow()
        return win.title if win else ""
    except: return ""

def _context_suggestion(window_title: str) -> str:
    """
    Give ONE smart suggestion based on active app.
    Only for specific useful apps — not generic ones.
    """
    t = window_title.lower()

    # Only suggest for these specific apps
    if "youtube"    in t: return "Sir, you are watching YouTube. Want me to search something specific?"
    if "vs code"    in t: return "Sir, VS Code is open. Need help with your code?"
    if "spotify"    in t: return "Sir, Spotify is open. Want a specific song?"
    if "whatsapp"   in t: return "Sir, WhatsApp is open. Need to send a message?"
    if "excel"      in t: return "Sir, Excel is open. Need help with formulas?"
    if "powerpoint" in t: return "Sir, PowerPoint is open. Want help with your slides?"

    # No suggestion for generic apps
    return ""

def _handle_wa(count: int):
    global _last_wa_count
    if count == _last_wa_count: return
    _last_wa_count = count

    key = f"wa:{count}"
    if key in _notif_history: return
    _notif_history.add(key)

    _speak(f"Sir, you have {count} unread WhatsApp message{'s' if count > 1 else'}'}.")

def _monitor_loop():
    global _running, _last_suggest, _last_app

    print("[SMART] Monitor active.")
    last_wa_check      = 0
    last_context_check = 0

    while _running:
        try:
            now = time.time()

            # WhatsApp check every 20 seconds
            if now - last_wa_check > 20:
                last_wa_check = now
                count = _get_wa_count()
                if count > 0:
                    threading.Thread(
                        target=_handle_wa, args=(count,), daemon=True
                    ).start()

            # Context suggestion — only every 5 minutes
            # AND only when app changes to a known app
            if now - last_context_check > 60:
                last_context_check = now
                title      = _get_active_window()
                # Only suggest if app actually changed
                if title and title != _last_app:
                    _last_app = title
                    if now - _last_suggest > SUGGESTION_COOLDOWN:
                        suggestion = _context_suggestion(title)
                        if suggestion:
                            _last_suggest = now
                            threading.Thread(
                                target=_speak, args=(suggestion,), daemon=True
                            ).start()

        except Exception as e:
            print(f"[SMART] Error: {e}")

        time.sleep(10)

def start_smart_assistant():
    global _running
    if _running: return
    _running = True
    threading.Thread(target=_monitor_loop, daemon=True).start()
    print("[SMART] Smart Assistant active.")

def stop_smart_assistant():
    global _running
    _running = False