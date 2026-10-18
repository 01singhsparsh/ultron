import threading, time, datetime, os, sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from modules.speaker import speak

_alerted    = {
    "battery_low":False,"battery_critical":False,"battery_charged":False,
    "morning":False,"afternoon":False,"evening":False,
    "study_time":False,"sleep_time":False,"cpu_high":False,
}
_last_reset = datetime.date.today()

def _reset_daily_flags():
    global _last_reset
    today = datetime.date.today()
    if today != _last_reset:
        for k in _alerted: _alerted[k] = False
        _last_reset = today

def _check_battery():
    try:
        import psutil
        b = psutil.sensors_battery()
        if not b: return
        pct = int(b.percent); plugged = b.power_plugged
        if pct <= 8 and not plugged and not _alerted["battery_critical"]:
            _alerted["battery_critical"] = True
            speak(f"Sir! Critical warning! Battery is at {pct} percent. Please plug in immediately.")
        elif pct <= 20 and not plugged and not _alerted["battery_low"]:
            _alerted["battery_low"] = True
            speak(f"Sir, battery is at {pct} percent. You may want to plug in.")
        elif pct >= 95 and plugged and not _alerted["battery_charged"]:
            _alerted["battery_charged"] = True
            speak("Sir, battery is fully charged. You can unplug now.")
        elif pct > 30:
            _alerted["battery_low"] = False
            _alerted["battery_critical"] = False
    except: pass

def _check_time():
    hour = datetime.datetime.now().hour
    minute = datetime.datetime.now().minute
    if hour == 8 and minute < 5 and not _alerted["morning"]:
        _alerted["morning"] = True
        speak("Good morning Sparsh Sir! Time to start your day. Shall I give you a briefing?")
    elif hour == 13 and minute < 5 and not _alerted["afternoon"]:
        _alerted["afternoon"] = True
        speak("Good afternoon Sparsh Sir. Hope your day is going well.")
    elif hour == 18 and minute < 5 and not _alerted["evening"]:
        _alerted["evening"] = True
        speak("Good evening Sparsh Sir. Shall I play some relaxing music?")
    elif hour == 20 and minute < 5 and not _alerted["study_time"]:
        _alerted["study_time"] = True
        speak("Sir, it is 8 PM. Good time to study. Shall I play focus music?")
    elif hour == 23 and minute < 5 and not _alerted["sleep_time"]:
        _alerted["sleep_time"] = True
        speak("Sir, it is getting late. You should consider getting some rest.")

def _proactive_loop():
    while True:
        try:
            _reset_daily_flags()
            _check_battery()
            _check_time()
        except Exception as e:
            print(f"Proactive error: {e}")
        time.sleep(120)  

def start_proactive():
    t = threading.Thread(target=_proactive_loop, daemon=True)
    t.start()
    print("[ULTRON] Proactive monitoring started.")