"""
gaming_mode.py
ULTRON AI Gaming Mode — Complete working version.
Launches Asphalt 9 → waits for load → starts gesture control.
Camera runs as small overlay — game stays in focus.
"""
import threading, time, sys, os, subprocess
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

_process  = None
_running  = False

ASPHALT_EXE = r"D:\Asphalt\Asphalt Legends\Content\Asphalt9_gdk_x64_rtl.exe"

def start_gaming_mode(game_name: str = "asphalt"):
    global _process, _running
    if _running:
        print("[GAMING] Already running")
        return
    _running = True
    launcher = os.path.join(BASE_DIR, "gaming_mode", "gaming_launcher.py")
    _write_launcher(launcher)
    try:
        _process = subprocess.Popen(
            ["py", "-3.11", launcher],
            cwd=BASE_DIR,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print(f"[GAMING] Started")
        threading.Thread(target=_monitor, daemon=True).start()
    except Exception as e:
        print(f"[GAMING] Launch error: {e}")
        _running = False

def _write_launcher(path: str):
    code = r'''
import sys, os, time, subprocess, ctypes
sys.path.insert(0, r"''' + BASE_DIR + r'''")

ASPHALT_EXE = r"D:\Asphalt\Asphalt Legends\Content\Asphalt9_gdk_x64_rtl.exe"
GAME_TITLE  = "Asphalt"

def focus_game():
    """Bring Asphalt window to front so keys go to it."""
    try:
        import pygetwindow as gw
        for win in gw.getAllWindows():
            if GAME_TITLE.lower() in win.title.lower():
                win.activate()
                return True
    except: pass
    return False

def launch_asphalt():
    """Launch Asphalt 9 directly via exe."""
    print("[GAMING] Launching Asphalt 9...")
    from modules.speaker import speak
    speak("Launching Asphalt 9 Legends Sir. Please wait.")
    try:
        subprocess.Popen(
            [ASPHALT_EXE],
            cwd=os.path.dirname(ASPHALT_EXE)
        )
        print("[GAMING] Asphalt process started.")
        return True
    except Exception as e:
        print(f"[GAMING] Launch error: {e}")
        speak("Could not launch Asphalt Sir. Please open it manually.")
        return False

def wait_for_game(timeout=60):
    """Wait until Asphalt window appears."""
    print("[GAMING] Waiting for Asphalt to load...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            import pygetwindow as gw
            for win in gw.getAllWindows():
                if GAME_TITLE.lower() in win.title.lower():
                    print(f"[GAMING] Game window found: {win.title}")
                    return True
        except: pass
        time.sleep(2)
    print("[GAMING] Timeout waiting for game.")
    return False

def run():
    from modules.speaker import speak

    # Step 1 — Launch game
    launched = launch_asphalt()
    if not launched:
        speak("Please open Asphalt manually Sir. I will start gesture control.")
        time.sleep(5)

    # Step 2 — Wait for game to load
    speak("Waiting for game to load Sir.")
    game_ready = wait_for_game(timeout=60)

    if game_ready:
        speak("Asphalt is ready Sir. Focusing game window.")
        time.sleep(1)
        focus_game()
        time.sleep(2)
    else:
        speak("Could not detect game window Sir. Starting gesture control anyway.")

    # Step 3 — Init camera
    import cv2
    import numpy as np

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS,          60)

    if not cap.isOpened():
        speak("Camera not available Sir.")
        return

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Step 4 — Init tracking
    from pipeline.hand_tracker            import HandTracker
    from pipeline.gesture_engine          import GestureEngine
    from gaming_mode.gesture_controller   import GestureController, release_all
    from gaming_mode.holographic_wheel    import HolographicWheel
    from gaming_mode.copilot              import RacingCopilot

    tracker    = HandTracker()
    gesture_e  = GestureEngine()
    controller = GestureController()
    wheel      = HolographicWheel(w, h)
    copilot    = RacingCopilot()

    speak("Ultron Gaming Mode active Sir. Show both hands to see the wheel.")

    # Step 5 — Create small overlay window (top-right corner)
    cv2.namedWindow("ULTRON HUD", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("ULTRON HUD", w, h)
    cv2.setWindowProperty("ULTRON HUD", cv2.WND_PROP_TOPMOST, 1)

    # Position top-right so it does not cover game
    screen_w = 1920
    cv2.moveWindow("ULTRON HUD", screen_w - w - 10, 10)

    speed          = 0
    fps_time       = time.time()
    fps            = 0
    frame_count    = 0
    last_focus     = time.time()

    print("[GAMING] Gesture control active! Q = quit")
    print("[GAMING] Fist=Accel | Palm=Brake | Tilt=Steer | Point=Nitro")

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue

        frame = cv2.flip(frame, 1)

        # Brightness correction
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg  = float(np.mean(gray))
        if avg < 85:
            factor = min(110.0 / max(avg, 1.0), 2.2)
            frame  = cv2.convertScaleAbs(frame, alpha=factor, beta=8)
        elif avg > 155:
            factor = max(105.0 / avg, 0.45)
            frame  = cv2.convertScaleAbs(frame, alpha=factor, beta=0)

        # Track hands
        hands_data   = tracker.process(frame)
        all_gestures = []

        for hand in hands_data:
            g = gesture_e.recognize(hand)
            if controller.recognize_peace(hand["landmarks"]):
                g.append({"name":"peace","confidence":0.9,"position":hand["palm"]})
            all_gestures.extend(g)

        # Refocus game every 8 seconds so keys go to Asphalt
        now = time.time()
        if now - last_focus > 8:
            last_focus = now
            if focus_game():
                # Small delay then bring HUD back on top
                time.sleep(0.1)
                cv2.setWindowProperty("ULTRON HUD", cv2.WND_PROP_TOPMOST, 1)

        # Process gesture controls — keys sent to focused game window
        controller.process(hands_data, all_gestures)
        status = controller.get_status()
        keys   = status.get("keys_pressed", [])

        # Speed simulation for HUD display
        if "w"     in keys: speed = min(speed + 3,   220)
        elif "s"   in keys: speed = max(speed - 9,     0)
        elif speed  > 0:    speed = max(speed - 2,     0)

        # Render holographic wheel
        frame = wheel.render(
            frame, hands_data,
            steering_angle = status.get("steering", 0),
            speed          = speed,
            status         = status
        )

        # Draw hand landmarks
        tracker.draw(frame, hands_data)

        # AI co-pilot
        copilot.analyze(status, speed, len(hands_data) > 0)

        # Status bar
        gesture_names  = [g["name"] for g in all_gestures]
        current_gesture= gesture_names[0].upper() if gesture_names else "READY"
        cv2.putText(frame,
            f"Q=QUIT | HANDS:{len(hands_data)} | {current_gesture}",
            (5, h-6), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100,100,100), 1)

        # FPS counter
        frame_count += 1
        if time.time() - fps_time >= 1.0:
            fps = frame_count; frame_count = 0; fps_time = time.time()
        cv2.putText(frame, f"FPS:{fps}", (5, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80,80,80), 1)

        cv2.imshow("ULTRON HUD", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            from modules.speaker import speak
            speak("Exiting gaming mode Sir.")
            break

    release_all()
    tracker.release()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run()
'''
    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)

def _monitor():
    global _running, _process
    if _process:
        _process.wait()
        _running = False
        print("[GAMING] Ended")

def stop_gaming_mode():
    global _process, _running
    _running = False
    if _process:
        try: _process.terminate()
        except: pass
        _process = None

def is_gaming_running():
    return _running