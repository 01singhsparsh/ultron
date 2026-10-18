"""
earth_bridge.py
Writes voice commands to a JSON file that earth.html polls every second.
This is how ULTRON voice reaches the browser window.
"""
import os, json, time

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CMD_FILE   = os.path.join(BASE_DIR, "data", "earth_cmd.json")

def send_to_earth(command: str):
    """Write command — browser polls this file."""
    try:
        with open(CMD_FILE, 'w') as f:
            json.dump({"cmd": command, "ts": time.time()}, f)
        print(f"[EARTH] Command sent: {command}")
    except Exception as e:
        print(f"[EARTH] Bridge error: {e}")