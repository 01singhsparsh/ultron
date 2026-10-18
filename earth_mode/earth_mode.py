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
    _server_started = True
    sys.path.insert(0, BASE_DIR)
    from earth_mode.earth_server import start_server
    start_server()
    time.sleep(0.8)

def _clear_cmd():
    try:
        with open(CMD_FILE,"w") as f: json.dump({},f)
    except: pass

def send_command(cmd):
    if not _active: return
    try:
        with open(CMD_FILE,"w") as f:
            json.dump({"cmd":cmd,"ts":time.time()},f)
        print(f"[EARTH] CMD -> {cmd}")
    except Exception as e: print(f"[EARTH] Error: {e}")

def start_earth_mode():
    global _active
    if _active: _speak("Earth mode already active Sir."); return
    _active = True
    _speak("Activating Earth Mode Sir.")
    _ensure_server()
    _clear_cmd()
    url = f"http://localhost:{PORT}/earth.html"
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
    _active = False
    send_command("exit")
    time.sleep(0.5)
    _clear_cmd()
    _speak("Earth Mode closed Sir.")

def is_active(): return _active

def handle_earth_command(text):
    t = text.lower().strip()
    if any(p in t for p in ["open earth mode","earth mode","maps mode","open maps mode","holographic earth","show earth","open earth","satellite view"]):
        threading.Thread(target=start_earth_mode, daemon=True).start()
        return True
    if not _active: return False
    for phrase in ["show me","take me to","go to","find","navigate to","fly to","zoom to","zoom in on"]:
        if phrase in t:
            location = t.split(phrase,1)[1].strip()
            if location: send_command(f"goto:{location}"); _speak(f"Navigating to {location} Sir."); return True
    if "my location" in t or "current location" in t:
        send_command("mylocation"); _speak("Finding your location Sir."); return True
    layer_map = {
        "satellite mode":"sat","satellite view":"sat","satellite":"sat",
        "hybrid":"hybrid","street view":"street","streets":"street",
        "terrain":"topo","dark mode":"dark","dark map":"dark","night mode":"dark",
    }
    for kw,layer in layer_map.items():
        if kw in t: send_command(f"layer:{layer}"); _speak(f"{kw} activated Sir."); return True
    if "3d" in t: send_command("3d"); _speak("Toggling 3D buildings Sir."); return True
    if any(p in t for p in ["reset view","reset earth","reset map"]): send_command("reset"); _speak("Resetting view Sir."); return True
    if "fly in" in t: send_command("fly"); return True
    if any(p in t for p in ["exit earth","close earth","exit maps","close maps"]): threading.Thread(target=stop_earth_mode,daemon=True).start(); return True
    return False
