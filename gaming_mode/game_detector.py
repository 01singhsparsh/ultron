"""
game_detector.py
Launches games using their actual executable paths.
"""
import subprocess, psutil, time, os

ASPHALT_EXE = r"D:\Asphalt\Asphalt Legends\Content\Asphalt9_gdk_x64_rtl.exe"

GAMES = {
    "asphalt":         ASPHALT_EXE,
    "asphalt 9":       ASPHALT_EXE,
    "asphalt legends": ASPHALT_EXE,
}

def launch_game(game_name: str) -> bool:
    name_lower = game_name.lower().strip()
    exe        = None

    for key, path in GAMES.items():
        if key in name_lower or name_lower in key:
            exe = path
            break

    if not exe:
        exe = ASPHALT_EXE  # Default to Asphalt

    if not os.path.exists(exe):
        print(f"[GAME] Exe not found: {exe}")
        return False

    try:
        subprocess.Popen([exe], cwd=os.path.dirname(exe))
        print(f"[GAME] Launched: {exe}")
        time.sleep(3)
        return True
    except Exception as e:
        print(f"[GAME] Launch error: {e}")
        return False

def get_game_window_title(game_name: str) -> str:
    return "Asphalt"

def is_racing_game(game_name: str) -> bool:
    return True

def detect_running_game() -> str:
    try:
        for proc in psutil.process_iter(['name']):
            if "asphalt" in proc.info['name'].lower():
                return "Asphalt 9"
    except: pass
    return ""