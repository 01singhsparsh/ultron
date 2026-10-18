"""
workspace_manager.py
Restores previous work sessions automatically.
Opens apps, websites, and files that were open in last session.
"""
import os, sys, time, subprocess
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def restore_workspace(session: dict):
    """Restore a work session — open apps and websites."""
    if not session: return

    snapshots = session.get("snapshots",[])
    if not snapshots: return

    # Get the last snapshot
    last_snap = snapshots[-1]
    windows   = last_snap.get("windows",[])

    opened = []
    for win_title in windows[:6]:
        title_lower = win_title.lower()

        # VS Code
        if "visual studio code" in title_lower or "code" in title_lower:
            if "vs code" not in opened:
                opened.append("vs code")
                _open_app("code")

        # Browser-based (ChatGPT, YouTube, GitHub etc)
        elif "chatgpt" in title_lower:
            _open_url("https://chatgpt.com")

        elif "youtube" in title_lower:
            _open_url("https://youtube.com")

        elif "github" in title_lower:
            _open_url("https://github.com")

        elif "localhost" in title_lower:
            _open_url("http://localhost:3000")

        # Spotify
        elif "spotify" in title_lower and "spotify" not in opened:
            opened.append("spotify")
            _open_app("Spotify")

        # WhatsApp
        elif "whatsapp" in title_lower and "whatsapp" not in opened:
            opened.append("whatsapp")
            subprocess.Popen(
                ["powershell","-Command","start-process whatsapp:"],
                creationflags=subprocess.CREATE_NO_WINDOW)

        # Terminal
        elif any(x in title_lower for x in ["terminal","powershell","cmd","command"]):
            if "terminal" not in opened:
                opened.append("terminal")
                _open_app("wt")

        time.sleep(0.5)

    print(f"[WORKSPACE] Restored: {opened}")

def _open_app(exe: str):
    try:
        subprocess.Popen(["start","",exe], shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW)
    except: pass

def _open_url(url: str):
    try:
        import webbrowser
        webbrowser.open(url)
        time.sleep(0.5)
    except: pass

def save_current_workspace():
    """Save current workspace state."""
    try:
        from context_engine.session_manager import log_activity
        from executor.screen_context        import get_open_apps
        apps = get_open_apps()
        log_activity(f"Workspace: {', '.join(apps[:5])}", category="workspace")
    except Exception as e:
        print(f"[WORKSPACE] Save error: {e}")