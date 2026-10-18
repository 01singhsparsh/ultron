"""
session_manager.py
Records and restores work sessions automatically.
Silently watches what you are doing and builds a session timeline.
"""
import os, sys, json, time, datetime, threading
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS_DIR = os.path.join(BASE_DIR, "data", "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

_current_session = {}
_recording       = False

def _get_session_file(date_str: str = None) -> str:
    if not date_str:
        date_str = str(datetime.date.today())
    return os.path.join(SESSIONS_DIR, f"session_{date_str}.json")

def _save_session():
    try:
        path = _get_session_file()
        with open(path, 'w') as f:
            json.dump(_current_session, f, indent=2, default=str)
    except Exception as e:
        print(f"[SESSION] Save error: {e}")

def _capture_snapshot() -> dict:
    """Capture current workspace state."""
    snapshot = {
        "timestamp": str(datetime.datetime.now()),
        "windows":   [],
        "processes": [],
        "active":    "",
    }
    try:
        import pygetwindow as gw
        wins = []
        seen = set()
        for win in gw.getAllWindows():
            t = win.title.strip()
            if t and len(t) > 2 and t not in seen:
                seen.add(t)
                wins.append(t)
        snapshot["windows"]  = wins[:12]
        active = gw.getActiveWindow()
        snapshot["active"]   = active.title if active else ""
    except: pass

    try:
        import psutil
        procs = []
        for proc in psutil.process_iter(['name','memory_percent']):
            try:
                if proc.info['memory_percent'] > 0.3:
                    procs.append(proc.info['name'])
            except: pass
        snapshot["processes"] = list(set(procs))[:10]
    except: pass

    return snapshot

def start_recording():
    """Start background session recording."""
    global _recording, _current_session

    if _recording: return
    _recording = True

    today = str(datetime.date.today())
    now   = str(datetime.datetime.now())

    # Load existing or create new
    path = _get_session_file()
    if os.path.exists(path):
        try:
            with open(path) as f:
                _current_session = json.load(f)
        except:
            _current_session = {}
    else:
        _current_session = {}

    _current_session.update({
        "date":       today,
        "start_time": _current_session.get("start_time", now),
        "snapshots":  _current_session.get("snapshots", []),
        "activities": _current_session.get("activities", []),
    })

    def _record_loop():
        while _recording:
            try:
                snap = _capture_snapshot()
                _current_session["snapshots"].append(snap)
                # Keep last 50 snapshots
                if len(_current_session["snapshots"]) > 50:
                    _current_session["snapshots"] = _current_session["snapshots"][-50:]
                _current_session["last_updated"] = str(datetime.datetime.now())
                _save_session()
            except Exception as e:
                print(f"[SESSION] Record error: {e}")
            time.sleep(30)  # Snapshot every 30 seconds

    threading.Thread(target=_record_loop, daemon=True).start()
    print("[SESSION] Recording started.")

def log_activity(activity: str, category: str = "general"):
    """Log a specific activity to current session."""
    global _current_session
    _current_session.setdefault("activities", []).append({
        "time":     str(datetime.datetime.now()),
        "activity": activity,
        "category": category,
    })
    # Keep last 100 activities
    if len(_current_session["activities"]) > 100:
        _current_session["activities"] = _current_session["activities"][-100:]
    _save_session()

def get_last_session(time_ref: str = "yesterday") -> dict:
    """Get a past session by time reference."""
    if time_ref == "yesterday":
        date = datetime.date.today() - datetime.timedelta(days=1)
    elif time_ref == "today":
        date = datetime.date.today()
    elif time_ref == "last_week":
        date = datetime.date.today() - datetime.timedelta(days=7)
    else:
        date = datetime.date.today() - datetime.timedelta(days=1)

    path = _get_session_file(str(date))
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except: pass

    # Search recent files
    for i in range(1, 8):
        d    = datetime.date.today() - datetime.timedelta(days=i)
        path = _get_session_file(str(d))
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except: pass

    return {}

def summarize_session(session: dict) -> str:
    """Generate a spoken summary of a session."""
    if not session:
        return "Sir, I could not find a previous session to restore."

    date       = session.get("date","unknown date")
    activities = session.get("activities",[])
    snapshots  = session.get("snapshots",[])

    # Get most common windows
    all_windows = []
    for snap in snapshots[-10:]:
        all_windows.extend(snap.get("windows",[]))

    from collections import Counter
    top_windows = [w for w,c in Counter(all_windows).most_common(4)]

    summary = f"Welcome back Sir. Your last session was on {date}. "

    if top_windows:
        summary += f"You were working with: {', '.join(top_windows[:3])}. "

    if activities:
        recent = activities[-3:]
        acts   = [a.get("activity","") for a in recent if a.get("activity")]
        if acts:
            summary += f"Recent activities: {'; '.join(acts[:2])}. "

    summary += "Shall I restore your workspace Sir?"
    return summary

def get_current_session() -> dict:
    return _current_session.copy()

def stop_recording():
    global _recording
    _recording = False
    _save_session()