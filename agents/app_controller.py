import subprocess, os, time, psutil

APP_MAP = {
    "chrome":"chrome.exe","google chrome":"chrome.exe",
    "brave":"brave.exe","firefox":"firefox.exe","edge":"msedge.exe",
    "notepad":"notepad.exe","vs code":"code.exe","vscode":"code.exe",
    "visual studio code":"code.exe","spotify":"Spotify.exe",
    "discord":"Discord.exe","whatsapp":"WhatsApp.exe",
    "calculator":"calc.exe","paint":"mspaint.exe",
    "word":"WINWORD.EXE","excel":"EXCEL.EXE","powerpoint":"POWERPNT.EXE",
    "task manager":"Taskmgr.exe","file explorer":"explorer.exe",
    "explorer":"explorer.exe","cmd":"cmd.exe","powershell":"powershell.exe",
    "terminal":"wt.exe","vlc":"vlc.exe","zoom":"Zoom.exe",
    "settings":"ms-settings:","camera":"microsoft.windows.camera:",
}

def open_app(app_name):
    app_lower = app_name.lower().strip()
    print(f"[APP_CTRL] Opening: {app_name}")
    if app_lower in APP_MAP:
        exe = APP_MAP[app_lower]
        if exe.endswith(":"):
            subprocess.Popen(f"start {exe}", shell=True); return True
        try: subprocess.Popen(["start","",exe], shell=True); return True
        except: pass
    try: subprocess.Popen(["start","",app_name], shell=True); time.sleep(0.5); return True
    except: pass
    print(f"[APP_CTRL] Could not open: {app_name}"); return False

def close_app(app_name):
    app_lower = app_name.lower().strip()
    exe       = APP_MAP.get(app_lower, f"{app_name}.exe")
    try:
        subprocess.call(f"taskkill /f /im {exe}", shell=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"[APP_CTRL] Close error: {e}"); return False

def focus_app(app_name):
    try:
        import pygetwindow as gw
        app_lower = app_name.lower()
        for title in gw.getAllTitles():
            if app_lower in title.lower() and title.strip():
                try:
                    win = gw.getWindowsWithTitle(title)[0]
                    win.restore(); win.activate(); time.sleep(0.3); return True
                except: continue
    except Exception as e:
        print(f"[APP_CTRL] Focus error: {e}")
    return False

def is_app_running(app_name):
    app_lower = app_name.lower()
    exe       = APP_MAP.get(app_lower, f"{app_name}.exe").lower()
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == exe: return True
    except: pass
    return False

def install_software(name):
    print(f"[APP_CTRL] Installing: {name}")
    try:
        result = subprocess.run(
            ["winget","install","--silent","--accept-source-agreements",
             "--accept-package-agreements", name],
            capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception as e:
        print(f"[APP_CTRL] Install error: {e}"); return False