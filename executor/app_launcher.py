"""
app_launcher.py
Launches desktop apps and verifies they opened.
"""
import os, sys, subprocess, time, json, psutil
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIAS_FILE = os.path.join(BASE_DIR,"executor","alias_database.json")

def _load_aliases() -> dict:
    try:
        with open(ALIAS_FILE) as f:
            return json.load(f).get("apps",{})
    except: return {}

def is_app_running(exe_name: str) -> bool:
    exe_lower = exe_name.lower().replace(".exe","")
    try:
        for proc in psutil.process_iter(['name']):
            n = proc.info['name'].lower().replace(".exe","")
            if n == exe_lower or exe_lower in n:
                return True
    except: pass
    return False

def _focus_window(app_name: str) -> bool:
    try:
        import pygetwindow as gw
        name_lower = app_name.lower()
        for win in gw.getAllWindows():
            if win.title and name_lower in win.title.lower():
                try: win.restore(); win.activate(); return True
                except: pass
    except: pass
    return False

def _launch_exe(exe_path: str) -> bool:
    try:
        if exe_path.endswith(":"):
            subprocess.Popen(f"start {exe_path}", shell=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        if os.path.exists(exe_path):
            subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        subprocess.Popen(["start","",exe_path], shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception as e:
        print(f"[LAUNCHER] Error: {e}"); return False

def launch_app(app_name: str) -> dict:
    aliases    = _load_aliases()
    name_lower = app_name.lower().strip()

    exe_candidates = aliases.get(name_lower,[])
    if not exe_candidates:
        for key,val in aliases.items():
            if key in name_lower or name_lower in key:
                exe_candidates = val; break

    if not exe_candidates:
        exe_candidates = [f"{app_name}.exe"]

    exe_name = exe_candidates[0]

    if is_app_running(exe_name):
        _focus_window(app_name)
        return {
            "success":True,
            "already_running":True,
            "message":f"{app_name.title()} is already open Sir.",
            "app":app_name
        }

    launched = False
    for candidate in exe_candidates:
        if _launch_exe(candidate):
            launched = True; break

    if not launched:
        return {"success":False,
                "message":f"Could not find {app_name} Sir.",
                "app":app_name}

    time.sleep(2)
    if not is_app_running(exe_name): time.sleep(3)

    _focus_window(app_name)
    return {"success":True,"already_running":False,
            "message":f"{app_name.title()} launched Sir.","app":app_name}

def close_app(app_name: str) -> dict:
    aliases    = _load_aliases()
    name_lower = app_name.lower().strip()
    exe        = aliases.get(name_lower,[f"{app_name}.exe"])[0]
    try:
        r = subprocess.call(f"taskkill /f /im {exe}",shell=True,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        return {"success":r==0,
                "message":f"{app_name.title()} {'closed Sir.' if r==0 else 'was not running Sir.'}"}
    except Exception as e:
        return {"success":False,"message":str(e)}

def get_running_apps() -> list:
    try:
        import pygetwindow as gw
        apps=[]; seen=set()
        for w in gw.getAllWindows():
            t=w.title.strip()
            if t and len(t)>1 and t not in seen:
                seen.add(t); apps.append(t)
        return apps[:15]
    except:
        apps=[]
        for proc in psutil.process_iter(['name']):
            try:
                n=proc.info['name']
                if n and n not in apps: apps.append(n)
            except: pass
        return apps[:15]