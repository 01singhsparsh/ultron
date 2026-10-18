"""
ultron_service.py
ULTRON OS — Launches widget + HUD only.
Voice engine started by clicking widget — not auto-started.
"""
import sys, os, time, threading, logging, ctypes, subprocess
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

if sys.platform == "win32":
    try:
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except: pass

LOG_FILE = os.path.join(BASE_DIR, "data", "ultron_service.log")
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE, level=logging.INFO,
    format="[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("SERVICE")

LOCK_FILE = os.path.join(BASE_DIR, "data", "ultron.lock")

def _check_single_instance() -> bool:
    import psutil
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE) as f: pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                log.info(f"Already running PID {pid}"); return False
            os.remove(LOCK_FILE)
        except: pass
    with open(LOCK_FILE, 'w') as f: f.write(str(os.getpid()))
    return True

def _cleanup():
    try:
        if os.path.exists(LOCK_FILE): os.remove(LOCK_FILE)
    except: pass

def _init_modules():
    def safe(name, fn):
        try: fn(); log.info(f"[OK] {name}")
        except Exception as e: log.error(f"[FAIL] {name}: {e}")
    safe("memory", lambda: __import__(
        'memory.memory_engine', fromlist=['init_db']).init_db())
    safe("proactive", lambda: __import__(
        'proactive', fromlist=['start_proactive']).start_proactive())
    safe("smart", lambda: __import__(
        'smart_assistant', fromlist=['start_smart_assistant']).start_smart_assistant())
    safe("session", lambda: __import__(
        'context_engine.session_manager', fromlist=['start_recording']).start_recording())

def _run_ui():
    from PyQt6.QtWidgets import QApplication
    from widget          import UltronCompanion
    import signal

    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("ULTRON OS")

    companion = UltronCompanion()

    # HUD
    try:
        from hud.hud_window  import IronManHUD
        from hud.hud_manager import register_hud
        hud = IronManHUD()
        register_hud(hud)
        log.info("HUD started.")
    except Exception as e:
        log.error(f"HUD error: {e}")

    # Launcher
    try:
        from hud.app_launcher_hud import init_launcher
        from hud.hud_manager      import register_launcher
        launcher = init_launcher(app)
        register_launcher(launcher)
        log.info("Launcher ready.")
    except Exception as e:
        log.error(f"Launcher error: {e}")

    # Show launcher after delay
    def _delayed():
        time.sleep(14)
        try:
            from modules.speaker import speak
            speak("Good to see you Sir. What are we working on today?")
            time.sleep(2)
        except Exception as e:
            log.error(f"Greeting: {e}")
        try:
            from hud.app_launcher_hud import show_launcher
            show_launcher()
        except Exception as e:
            log.error(f"Launcher show: {e}")

    threading.Thread(target=_delayed, daemon=True).start()

    def _shutdown(sig=None, frame=None):
        _cleanup()
        try: companion._save_position()
        except: pass
        app.quit()

    try:
        signal.signal(signal.SIGTERM, _shutdown)
        signal.signal(signal.SIGINT,  _shutdown)
    except: pass

    sys.exit(app.exec())

def main():
    log.info("=== ULTRON OS Starting ===")
    if not _check_single_instance(): sys.exit(0)
    try:
        time.sleep(8)
        _init_modules()
        _run_ui()
    except Exception as e:
        log.error(f"Fatal: {e}")
        _cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()