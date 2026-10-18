"""
earth_mode.py
ULTRON Earth Mode — launches server + browser, bridges voice commands.
"""
import os, sys, subprocess, threading, time, json, webbrowser

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CMD_FILE   = os.path.join(BASE_DIR, "data", "earth_cmd.json")
PORT       = 8765
_active    = False
_server_started = False

def _speak(text):
    try:
        from modules.speaker import speak
        speak(text)
    except: print(f"[EARTH] {text}")

def _ensure_server():
    global _server_started
    if _server_started: return
    _server_started = True
    from earth_mode.earth_server import start_server
    start_server()
    time.sleep(0.5)

def _clear_cmd():
    try:
        with open(CMD_FILE, "w") as f: json.dump({}, f)
    except: pass

def send_command(cmd: str):
    if not _active: return
    try:
        with open(CMD_FILE, "w") as f:
            json.dump({"cmd": cmd, "ts": time.time()}, f)
        print(f"[EARTH] CMD → {cmd}")
    except Exception as e:
        print(f"[EARTH] Bridge error: {e}")

def start_earth_mode():
    global _active
    if _active:
        _speak("Earth mode is already active Sir.")
        return
    _active = True
    _speak("Activating Earth Mode Sir.")

    _ensure_server()
    _clear_cmd()

    url = f"http://localhost:{PORT}/earth.html"
    # Try Brave/Chrome for best WebGL support
    launched = False
    for path in [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ.get("LOCALAPPDATA",""),
                     "BraveSoftware\\Brave-Browser\\Application\\brave.exe"),
    ]:
        if os.path.exists(path):
            subprocess.Popen(
                [path, "--new-window", "--start-maximized", url],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            launched = True
            break

    if not launched:
        webbrowser.open(url)

    time.sleep(1)
    _speak("Earth Mode ready Sir. Click the Earth to enter satellite view.")

def stop_earth_mode():
    global _active
    _active = False
    send_command("exit")
    time.sleep(0.5)
    _clear_cmd()
    _speak("Earth Mode closed Sir.")

def is_active() -> bool:
    return _active

def handle_earth_command(text: str) -> bool:
    t = text.lower().strip()

    # Activate triggers
    if any(p in t for p in [
        "open earth mode","earth mode","maps mode","open maps mode",
        "holographic earth","show earth","open earth","satellite view",
        "open satellite"
    ]):
        threading.Thread(target=start_earth_mode, daemon=True).start()
        return True

    if not _active: return False

    # Navigation commands
    for phrase in ["show me","take me to","go to","find","navigate to","fly to","zoom to","zoom in on"]:
        if phrase in t:
            location = t.split(phrase, 1)[1].strip()
            if location:
                send_command(f"goto:{location}")
                _speak(f"Navigating to {location} Sir.")
                return True

    # Special locations
    if "my location" in t or "current location" in t:
        send_command("mylocation")
        _speak("Finding your location Sir.")
        return True

    # Layer commands
    layer_map = {
        "satellite mode": "sat", "satellite view": "sat", "satellite": "sat",
        "hybrid mode": "hybrid", "hybrid": "hybrid",
        "street view": "street", "street mode": "street", "streets": "street",
        "terrain mode": "topo", "topo mode": "topo", "terrain": "topo",
        "dark mode": "dark", "dark map": "dark",
        "night mode": "dark",
    }
    for keyword, layer in layer_map.items():
        if keyword in t:
            send_command(f"layer:{layer}")
            _speak(f"{keyword.title()} activated Sir.")
            return True

    # 3D toggle
    if "3d buildings" in t or "three d" in t or "3 d" in t:
        send_command("3d")
        _speak("Toggling 3D buildings Sir.")
        return True

    # Reset
    if any(p in t for p in ["reset view","reset earth","reset map","orbital view"]):
        send_command("reset")
        _speak("Resetting view Sir.")
        return True

    # Fly in
    if "fly in" in t or "enter earth" in t or "enter orbit" in t:
        send_command("fly")
        _speak("Flying into Earth orbit Sir.")
        return True

    # Exit
    if any(p in t for p in ["exit earth","close earth","exit maps","close maps","exit mode"]):
        threading.Thread(target=stop_earth_mode, daemon=True).start()
        return True

    return False
