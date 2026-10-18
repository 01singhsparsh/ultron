"""
startup_manager.py
ULTRON OS Startup Manager
Initializes all subsystems in correct order.
No console. No terminal. Silent background service.
"""
import os, sys, time, threading, logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "data", "ultron.log")
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

# Logging to file only — no console output
logging.basicConfig(
    filename  = LOG_FILE,
    level     = logging.INFO,
    format    = "[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt   = "%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("ULTRON")

# Module status tracking
MODULE_STATUS = {
    "memory":   False,
    "voice":    False,
    "proactive":False,
    "smart":    False,
    "session":  False,
    "face":     False,
    "listener": False,
}

def _safe_init(name: str, fn):
    """Initialize a module safely — retry once on failure."""
    global MODULE_STATUS
    try:
        fn()
        MODULE_STATUS[name] = True
        log.info(f"[OK] {name} initialized")
        return True
    except Exception as e:
        log.warning(f"[RETRY] {name} failed: {e} — retrying in 3s")
        time.sleep(3)
        try:
            fn()
            MODULE_STATUS[name] = True
            log.info(f"[OK] {name} initialized (retry)")
            return True
        except Exception as e2:
            log.error(f"[FAIL] {name}: {e2}")
            MODULE_STATUS[name] = False
            return False

def init_memory():
    from memory.memory_engine import init_db
    init_db()

def init_voice():
    from modules.speaker import speak
    # Pre-warm the speech engine
    speak("")

def init_proactive():
    from proactive import start_proactive
    start_proactive()

def init_smart():
    from smart_assistant import start_smart_assistant
    start_smart_assistant()

def init_session():
    from context_engine.session_manager import start_recording
    start_recording()

def init_listener():
    import speech_recognition as sr
    r = sr.Recognizer()
    r.energy_threshold = 50

def initialize_all() -> dict:
    """Initialize all modules in parallel where possible."""
    log.info("=== ULTRON OS Starting ===")

    # Sequential critical modules
    _safe_init("memory",   init_memory)

    # Parallel non-critical modules
    threads = [
        threading.Thread(target=_safe_init, args=("voice",    init_voice),    daemon=True),
        threading.Thread(target=_safe_init, args=("proactive", init_proactive),daemon=True),
        threading.Thread(target=_safe_init, args=("session",  init_session),  daemon=True),
        threading.Thread(target=_safe_init, args=("listener", init_listener), daemon=True),
    ]
    for t in threads: t.start()
    for t in threads: t.join(timeout=10)

    # Smart assistant last
    _safe_init("smart", init_smart)

    ok    = sum(1 for v in MODULE_STATUS.values() if v)
    total = len(MODULE_STATUS)
    log.info(f"Startup complete: {ok}/{total} modules ready")
    return MODULE_STATUS.copy()

def get_status() -> dict:
    return MODULE_STATUS.copy()