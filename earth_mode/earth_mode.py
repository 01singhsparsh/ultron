import os, sys, subprocess, threading, time, json, webbrowser
BASE_DIR  = r"C:\ultron\ultron"
CMD_FILE  = os.path.join(BASE_DIR, "data", "earth_cmd.json")
PORT      = 8765
_active   = False
_server_started = False

def _speak(text):
    try:
        sys.path.insert(0, BASE_DIR)
        from modules.speaker import speak
        speak(text)
    except: print(f"[EARTH] {text}")

def _ensure_server():
    global _server_started
    if _server_started: return
    sys.path.insert(0, BASE_DIR)
    from earth_mode.earth_server import start_server
    start_server()
    _server_started = True      # only mark started AFTER it really started
    time.sleep(0.8)

def _clear_cmd():
    try:
        os.makedirs(os.path.dirname(CMD_FILE), exist_ok=True)
        with open(CMD_FILE,"w") as f: json.dump({},f)
    except: pass

def send_command(cmd):
    if not _active: return
    try:
        os.makedirs(os.path.dirname(CMD_FILE), exist_ok=True)
        with open(CMD_FILE,"w") as f:
            json.dump({"cmd":cmd,"ts":time.time()},f)
        print(f"[EARTH] CMD -> {cmd}")
    except Exception as e: print(f"[EARTH] Error: {e}")

def start_earth_mode():
    global _active
    if _active: _speak("Earth mode already active Sir."); return
    _active = True
    _speak("Activating Earth Mode Sir.")
    try:
        _ensure_server()
    except Exception as e:
        print(f"[EARTH] Could not start the Earth server: {e}")
        _active = False
        _speak("Earth server failed to start Sir.")
        return
    _clear_cmd()
    url = f"http://localhost:{PORT}/earth.html?v={int(time.time())}"
    launched = False
    for path in [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ.get("LOCALAPPDATA",""), r"BraveSoftware\Brave-Browser\Application\brave.exe"),
    ]:
        if os.path.exists(path):
            subprocess.Popen([path,"--new-window","--start-maximized",url], creationflags=subprocess.CREATE_NO_WINDOW)
            launched = True; break
    if not launched: webbrowser.open(url)
    time.sleep(1)
    _speak("Earth Mode ready Sir. Click the Earth to enter orbit.")

def stop_earth_mode():
    global _active
    send_command("exit")        # must be sent while still active
    _active = False
    time.sleep(0.5)
    _clear_cmd()
    _speak("Earth Mode closed Sir.")

def is_active(): return _active

def handle_earth_command(text):
    t = text.lower().strip()
    # exit phrases FIRST - "close earth mode" also contains "earth mode" and must not re-open it
    if _active and any(p in t for p in ["exit earth","close earth","exit maps","close maps"]):
        threading.Thread(target=stop_earth_mode,daemon=True).start(); return True
    open_phrases = ["open earth mode","earth mode","maps mode","open maps mode","holographic earth","show earth","open earth","satellite view"]
    if _active: open_phrases = [p for p in open_phrases if p != "satellite view"]   # once open, "satellite view" = switch layer
    if any(p in t for p in open_phrases):
        threading.Thread(target=start_earth_mode, daemon=True).start()
        return True
    if not _active: return False

    # ---- set / refresh YOUR location  ("i am at chandigarh university") ----
    # (checked BEFORE "show me"/"my location" so it is never mistaken for navigation)
    for phrase in ["i am currently at","i am at","i'm at","i am in","i'm in","my location is","set my location to","set my location as","set location to"]:
        if phrase in t:
            place = t.split(phrase,1)[1].strip(" .,!?")
            if place:
                send_command(f"setloc:{place}"); _speak(f"Setting your location to {place} Sir."); return True
    if any(p in t for p in ["recalibrate","refresh my location","refresh location","update my location","where am i","my location","current location","live location"]):
        send_command("recalibrate"); _speak("Refreshing your live location Sir."); return True

    # ---- directions from your location to the last place you visited ----
    # (checked BEFORE "show me" so "show me directions" is not treated as a place name)
    if "direction" in t:
        send_command("direction"); _speak("Showing directions from your location Sir."); return True

    # ---- navigate to a place ----
    for phrase in ["show me","take me to","go to","find","navigate to","fly to","zoom to","zoom in on"]:
        if phrase in t:
            location = t.split(phrase,1)[1].strip(" .,!?")
            if location: send_command(f"goto:{location}"); _speak(f"Navigating to {location} Sir."); return True

    # ---- view layers ----
    layer_map = {
        "satellite mode":"sat","satellite view":"sat","satellite":"sat","hybrid":"sat",
        "night mode":"layer:night","dark mode":"layer:night","dark map":"layer:night",
        "street view":"layer:day","streets":"layer:day","terrain":"layer:day","day mode":"layer:day","day view":"layer:day",
    }
    for kw,cmd in layer_map.items():
        if kw in t: send_command(cmd); _speak(f"{kw} activated Sir."); return True
    if "3d" in t: send_command("3d"); _speak("Toggling 3D buildings Sir."); return True
    if any(p in t for p in ["reset view","reset earth","reset map"]): send_command("reset"); _speak("Resetting view Sir."); return True
    if "fly in" in t: send_command("fly"); return True
    if any(p in t for p in ["exit earth","close earth","exit maps","close maps"]): threading.Thread(target=stop_earth_mode,daemon=True).start(); return True
    return False
