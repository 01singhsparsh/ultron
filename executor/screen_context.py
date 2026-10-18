"""
screen_context.py
Tells ULTRON what is currently on screen.
Uses window list + process list — NOT internet search.
"""
import psutil

def get_open_apps() -> list:
    """Get list of currently open applications with windows."""
    try:
        import pygetwindow as gw
        apps = []
        seen = set()
        for win in gw.getAllWindows():
            t = win.title.strip()
            if t and len(t) > 2 and t not in seen:
                # Filter out system noise
                skip = ["program manager","default ime","msctfime ui",
                        "gdi+","battery meter","windows input"]
                if not any(s in t.lower() for s in skip):
                    seen.add(t)
                    apps.append(t)
        return apps[:12]
    except: pass
    return []

def get_active_window() -> str:
    """Get the currently focused window title."""
    try:
        import pygetwindow as gw
        win = gw.getActiveWindow()
        return win.title if win else ""
    except: return ""

def get_running_processes() -> list:
    """Get top running processes."""
    try:
        procs = []
        for proc in psutil.process_iter(['name','memory_percent']):
            try:
                if proc.info['memory_percent'] > 0.2:
                    procs.append(proc.info['name'])
            except: pass
        return list(set(procs))[:10]
    except: return []

def describe_screen() -> str:
    """
    Return a human-readable description of what is on screen.
    This is what ULTRON says when asked "what's on my screen".
    """
    open_apps   = get_open_apps()
    active      = get_active_window()
    processes   = get_running_processes()

    # Friendly app name mapping
    friendly = {
        "brave":    "Brave Browser",
        "chrome":   "Google Chrome",
        "code":     "VS Code",
        "discord":  "Discord",
        "spotify":  "Spotify",
        "whatsapp": "WhatsApp",
        "explorer": "File Explorer",
        "notepad":  "Notepad",
    }

    # Build description
    description = ""

    if active:
        description += f"You are currently focused on: {active}.\n"

    if open_apps:
        # Clean up titles
        clean_apps = []
        for app in open_apps[:8]:
            if " - " in app:
                parts = app.split(" - ")
                clean_apps.append(parts[-1].strip() or parts[0].strip())
            else:
                clean_apps.append(app)
        # Deduplicate
        clean_apps = list(dict.fromkeys(clean_apps))[:6]
        description += f"Open windows: {', '.join(clean_apps)}."
    else:
        description += "No windows detected."

    return description

def is_app_open(app_name: str) -> bool:
    """Check if a specific app is currently open."""
    name_lower = app_name.lower()
    for win_title in get_open_apps():
        if name_lower in win_title.lower():
            return True
    return False