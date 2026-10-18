"""
install_startup.py
One-time setup script.
Registers ULTRON with Windows Task Scheduler.
Run this ONCE as Administrator.
After this — ULTRON starts automatically with Windows forever.
"""
import os, sys, subprocess, ctypes

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PY_EXE     = r"C:\Users\ASUS\AppData\Local\Programs\Python\Python311\pythonw.exe"
SERVICE    = os.path.join(BASE_DIR, "ultron_service.py")
TASK_NAME  = "ULTRON_OS"

def is_admin() -> bool:
    try:    return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def remove_old_tasks():
    for name in ["ULTRON_OS", "ULTRON_Companion", "ULTRON_Widget"]:
        subprocess.run(
            ["schtasks", "/delete", "/tn", name, "/f"],
            capture_output=True
        )
    print("[SETUP] Old tasks removed.")

def create_task():
    """Create Task Scheduler entry using XML — most reliable method."""
    xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT8S</Delay>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <RestartOnFailure>
      <Interval>PT2M</Interval>
      <Count>5</Count>
    </RestartOnFailure>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{PY_EXE}</Command>
      <Arguments>"{SERVICE}"</Arguments>
      <WorkingDirectory>{BASE_DIR}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''

    xml_path = os.path.join(BASE_DIR, "data", "ultron_task.xml")
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

    with open(xml_path, 'w', encoding='utf-16') as f:
        f.write(xml)

    result = subprocess.run(
        ["schtasks", "/create", "/tn", TASK_NAME, "/xml", xml_path, "/f"],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        print(f"[SETUP] Task '{TASK_NAME}' created successfully!")
        return True
    else:
        print(f"[SETUP] XML method failed: {result.stderr}")
        return _fallback_task()

def _fallback_task():
    """Fallback using PowerShell New-ScheduledTask."""
    print("[SETUP] Trying PowerShell method...")
    ps_cmd = f'''
$action   = New-ScheduledTaskAction -Execute '{PY_EXE}' -Argument '"{SERVICE}"' -WorkingDirectory '{BASE_DIR}'
$trigger  = New-ScheduledTaskTrigger -AtLogon
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 2) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest -LogonType Interactive
Register-ScheduledTask -TaskName "{TASK_NAME}" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
'''
    result = subprocess.run(
        ["powershell", "-Command", ps_cmd],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("[SETUP] PowerShell method succeeded!")
        return True
    else:
        print(f"[SETUP] PowerShell failed: {result.stderr}")
        return False

def verify_task() -> bool:
    result = subprocess.run(
        ["schtasks", "/query", "/tn", TASK_NAME],
        capture_output=True, text=True
    )
    return result.returncode == 0

def add_exclusions():
    paths = [
        r"C:\Users\ASUS\AppData\Local\Programs\Python\Python311",
        BASE_DIR,
    ]
    processes = ["pythonw.exe", "py.exe", "python.exe"]
    for path in paths:
        subprocess.run(
            ["powershell", "-Command",
             f'Add-MpPreference -ExclusionPath "{path}" -ErrorAction SilentlyContinue'],
            capture_output=True
        )
    for proc in processes:
        subprocess.run(
            ["powershell", "-Command",
             f'Add-MpPreference -ExclusionProcess "{proc}" -ErrorAction SilentlyContinue'],
            capture_output=True
        )
    print("[SETUP] Windows Defender exclusions added.")

def remove_startup_folder():
    """Remove old shortcut from Startup folder."""
    try:
        startup = os.path.join(
            os.environ.get("APPDATA",""),
            r"Microsoft\Windows\Start Menu\Programs\Startup"
        )
        for fname in ["ULTRON_Widget.lnk", "ULTRON.lnk"]:
            lnk = os.path.join(startup, fname)
            if os.path.exists(lnk):
                os.remove(lnk)
                print(f"[SETUP] Removed: {fname}")
    except: pass

def start_now():
    """Start ULTRON right now without restarting."""
    print("[SETUP] Starting ULTRON now...")
    try:
        subprocess.Popen(
            [PY_EXE, SERVICE],
            cwd           = BASE_DIR,
            creationflags = subprocess.DETACHED_PROCESS |
                           subprocess.CREATE_NO_WINDOW
        )
        print("[SETUP] ULTRON started!")
        return True
    except Exception as e:
        print(f"[SETUP] Could not start: {e}")
        # Try via schtasks run
        result = subprocess.run(
            ["schtasks", "/run", "/tn", TASK_NAME],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("[SETUP] Started via Task Scheduler!")
            return True
        return False

def main():
    print("=" * 50)
    print("ULTRON OS — Startup Installation")
    print("=" * 50)
    print(f"[SETUP] Python:  {PY_EXE}")
    print(f"[SETUP] Service: {SERVICE}")
    print(f"[SETUP] Exists:  {os.path.exists(PY_EXE)}")

    if not os.path.exists(PY_EXE):
        print(f"\n[ERROR] pythonw.exe not found at: {PY_EXE}")
        print("Please update PY_EXE path in this file.")
        input("Press Enter to exit...")
        sys.exit(1)

    if not is_admin():
        print("\n[ERROR] Please run as Administrator!")
        print("Right-click PowerShell → Run as Administrator")
        input("Press Enter to exit...")
        sys.exit(1)

    remove_old_tasks()
    remove_startup_folder()
    add_exclusions()
    success = create_task()

    if verify_task():
        print("\n✅ ULTRON OS installed successfully!")
        print("✅ Will auto-start 8 seconds after next Windows login.")
        print(f"\nPython: {PY_EXE}")
        print(f"Service: {SERVICE}")
        print("\nStart ULTRON right now?")
        choice = input("Press Y to start now, any key to skip: ").strip().lower()
        if choice == 'y':
            start_now()
    else:
        print("\n❌ Task creation failed.")
        print("Try running PowerShell as Administrator and run again.")

    input("\nPress Enter to close...")

if __name__ == "__main__":
    main()