"""
window_manager.py
Manages open windows — minimize, maximize, close, focus.
Uses pygetwindow for real window manipulation.
"""
import time

def _find_window(name: str):
    """Find a window by partial title match."""
    try:
        import pygetwindow as gw
        name_lower = name.lower()
        # Exact first
        for win in gw.getAllWindows():
            if win.title and win.title.lower() == name_lower:
                return win
        # Partial
        for win in gw.getAllWindows():
            if win.title and name_lower in win.title.lower():
                return win
    except: pass
    return None

def minimize_window(app_name: str) -> dict:
    win = _find_window(app_name)
    if not win:
        return {"success": False, "message": f"Could not find {app_name} window."}
    try:
        win.minimize()
        return {"success": True, "message": f"{app_name} minimized."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def maximize_window(app_name: str) -> dict:
    win = _find_window(app_name)
    if not win:
        return {"success": False, "message": f"Could not find {app_name} window."}
    try:
        win.maximize()
        return {"success": True, "message": f"{app_name} maximized."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def restore_window(app_name: str) -> dict:
    win = _find_window(app_name)
    if not win:
        return {"success": False, "message": f"Could not find {app_name} window."}
    try:
        win.restore()
        win.activate()
        return {"success": True, "message": f"{app_name} restored."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def close_window(app_name: str) -> dict:
    win = _find_window(app_name)
    if not win:
        return {"success": False, "message": f"Could not find {app_name} window."}
    try:
        win.close()
        return {"success": True, "message": f"{app_name} closed."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def focus_window(app_name: str) -> dict:
    win = _find_window(app_name)
    if not win:
        return {"success": False, "message": f"Could not find {app_name} window."}
    try:
        win.restore()
        win.activate()
        return {"success": True, "message": f"Switched to {app_name}."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def show_desktop() -> dict:
    try:
        import subprocess
        subprocess.call(
            'powershell -command "(New-Object -ComObject Shell.Application).ToggleDesktop()"',
            shell=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        return {"success": True, "message": "Desktop shown."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_all_windows() -> list:
    """Get all open window titles."""
    try:
        import pygetwindow as gw
        titles = []
        seen   = set()
        for win in gw.getAllWindows():
            t = win.title.strip()
            if t and len(t) > 1 and t not in seen:
                seen.add(t)
                titles.append(t)
        return titles
    except: return []

def execute_window_action(action: str, app_name: str) -> dict:
    """Route to correct window action."""
    action_lower = action.lower()
    if "minimize" in action_lower:  return minimize_window(app_name)
    if "maximize" in action_lower:  return maximize_window(app_name)
    if "maximize" in action_lower:  return maximize_window(app_name)
    if "restore"  in action_lower:  return restore_window(app_name)
    if "close"    in action_lower:  return close_window(app_name)
    if "focus"    in action_lower:  return focus_window(app_name)
    if "switch"   in action_lower:  return focus_window(app_name)
    if "desktop"  in action_lower:  return show_desktop()
    return focus_window(app_name)