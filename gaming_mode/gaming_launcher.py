import sys, os, time, subprocess, math
sys.path.insert(0, r"C:\ultron\ultron")

ASPHALT_EXE = r"D:\Asphalt\Asphalt Legends\Content\Asphalt9_gdk_x64_rtl.exe"
GAME_TITLE  = "Asphalt"

# ── Steering state ──
_smooth_steer     = 0.0
_calibrated_angle = None
_prev_keys        = set()
DEAD_ZONE         = 0.08
SMOOTH_FACTOR     = 0.25
STEER_THRESHOLD   = 0.15

try:
    import pynput.keyboard as pk
    _kb = pk.Controller()
    USE_PYNPUT = True
except:
    USE_PYNPUT = False

def _press(key):
    if key not in _prev_keys:
        _prev_keys.add(key)
        try:
            if USE_PYNPUT: _kb.press(key)
            else:
                import pyautogui
                pyautogui.keyDown(key)
        except: pass

def _release(key):
    if key in _prev_keys:
        _prev_keys.discard(key)
        try:
            if USE_PYNPUT: _kb.release(key)
            else:
                import pyautogui
                pyautogui.keyUp(key)
        except: pass

def _release_all():
    for k in list(_prev_keys): _release(k)

def focus_game():
    try:
        import pygetwindow as gw
        for win in gw.getAllWindows():
            if GAME_TITLE.lower() in win.title.lower():
                win.activate()
                return True
    except: pass
    return False

def get_steering(hands_data) -> float:
    global _smooth_steer, _calibrated_angle

    if len(hands_data) >= 2:
        sorted_h = sorted(hands_data, key=lambda h: h['palm'][0])
        lh, rh   = sorted_h[0], sorted_h[1]
        dx = rh['palm'][0] - lh['palm'][0]
        dy = rh['palm'][1] - lh['palm'][1]
        angle = math.degrees(math.atan2(dy, dx))

        if _calibrated_angle is None:
            _calibrated_angle = angle

        deviation  = angle - _calibrated_angle
        deviation  = max(-45, min(45, deviation))
        raw_steer  = deviation / 45.0

    elif len(hands_data) == 1:
        palm_x     = hands_data[0]['palm'][0]
        frame_cx   = 160
        raw_steer  = (palm_x - frame_cx) / frame_cx
        raw_steer  = max(-1.0, min(1.0, raw_steer))

    else:
        _smooth_steer *= 0.85
        if abs(_smooth_steer) < 0.02: _smooth_steer = 0.0
        return _smooth_steer

    if abs(raw_steer) < DEAD_ZONE:
        raw_steer = 0.0

    _smooth_steer = _smooth_steer * (1-SMOOTH_FACTOR) + raw_steer * SMOOTH_FACTOR
    return round(_smooth_steer, 3)

def apply_steering(steer):
    if steer < -STEER_THRESHOLD:
        _press('a'); _release('d')
    elif steer > STEER_THRESHOLD:
        _press('d'); _release('a')
    else:
        _release('a'); _release('d')

def draw_wheel(frame, cx, cy, radius, angle_deg, steer, state):
    import cv2
    COLORS = {
        "accel":(50,230,50), "brake":(50,50,230),
        "nitro":(255,100,50), "idle":(0,210,230)
    }
    col = COLORS.get(state, COLORS["idle"])
    cx, cy, radius = int(cx), int(cy), int(radius)

    # Glow
    for extra in [10, 6, 3]:
        ov = frame.copy()
        cv2.circle(ov, (cx,cy), radius+extra, col, 2)
        cv2.addWeighted(ov, 0.2, frame, 0.8, 0, frame)

    # Outer ring
    cv2.circle(frame, (cx,cy), radius,     col, 3)
    cv2.circle(frame, (cx,cy), radius-9,   col, 1)

    # 3 Spokes — rotate with angle
    for i in range(3):
        rad = math.radians(angle_deg + i*120)
        x1  = int(cx + 15   * math.cos(rad))
        y1  = int(cy + 15   * math.sin(rad))
        x2  = int(cx + (radius-7) * math.cos(rad))
        y2  = int(cy + (radius-7) * math.sin(rad))
        cv2.line(frame, (x1,y1), (x2,y2), col, 3)
        ov = frame.copy()
        cv2.line(ov, (x1,y1), (x2,y2), col, 8)
        cv2.addWeighted(ov, 0.18, frame, 0.82, 0, frame)

    # Grip pads
    for i in range(6):
        rad = math.radians(angle_deg + i*60 + 30)
        px  = int(cx + radius * math.cos(rad))
        py  = int(cy + radius * math.sin(rad))
        cv2.circle(frame, (px,py), 6, col, -1)

    # Center hub — pulsing
    pulse = int(13 + 2*math.sin(time.time()*5))
    cv2.circle(frame, (cx,cy), pulse+5, tuple(int(c*0.25) for c in col), -1)
    cv2.circle(frame, (cx,cy), pulse,   col, -1)
    cv2.circle(frame, (cx,cy), 5,       (255,255,255), -1)

    # Steering bar below wheel
    bar_w  = radius * 2
    bar_y  = cy + radius + 18
    bar_x  = cx - radius
    cv2.rectangle(frame, (bar_x,bar_y-5), (bar_x+bar_w,bar_y+5), (30,30,30), -1)
    cv2.rectangle(frame, (bar_x,bar_y-5), (bar_x+bar_w,bar_y+5), (60,60,60),  1)
    ind_x  = int(cx + steer*radius)
    ind_x  = max(bar_x, min(bar_x+bar_w, ind_x))
    ind_col= (50,230,50) if abs(steer)<0.15 else (0,200,255) if abs(steer)<0.5 else (50,50,230)
    cv2.circle(frame, (ind_x,bar_y), 9, ind_col, -1)
    cv2.line(frame, (cx,bar_y-10), (cx,bar_y+10), (80,80,80), 2)
    cv2.putText(frame, "L", (bar_x-14,bar_y+5),   cv2.FONT_HERSHEY_SIMPLEX, 0.4, col, 1)
    cv2.putText(frame, "R", (bar_x+bar_w+4,bar_y+5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, col, 1)
    cv2.putText(frame, f"{steer:+.2f}", (cx-20,bar_y+22), cv2.FONT_HERSHEY_SIMPLEX, 0.38, col, 1)

    # State label above wheel
    cv2.putText(frame, state.upper(), (cx-25,cy-radius-8),
               cv2.FONT_HERSHEY_SIMPLEX, 0.4, col, 1)

def calibrate(cap, tracker):
    import cv2
    from modules.speaker import speak
    global _calibrated_angle

    speak("Hold your hands on the wheel naturally. Calibrating steering center.")
    _calibrated_angle = None
    angles  = []
    start   = time.time()

    while time.time() - start < 3:
        ret, frame = cap.read()
        if not ret: continue
        frame      = cv2.flip(frame, 1)
        hands_data = tracker.process(frame)

        w, h = frame.shape[1], frame.shape[0]
        cv2.putText(frame, "CALIBRATING — HOLD POSITION",
                   (10, h//2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)
        bar = int((time.time()-start)/3.0 * w)
        cv2.rectangle(frame, (0,h-8), (bar,h), (0,255,255), -1)
        cv2.imshow("ULTRON HUD", frame)
        cv2.waitKey(1)

        if len(hands_data) >= 2:
            sh   = sorted(hands_data, key=lambda h: h['palm'][0])
            lh,rh= sh[0], sh[1]
            dx   = rh['palm'][0] - lh['palm'][0]
            dy   = rh['palm'][1] - lh['palm'][1]
            angles.append(math.degrees(math.atan2(dy, dx)))

    if angles:
        _calibrated_angle = sum(angles)/len(angles)
        speak(f"Calibrated. Go Sir.")
        print(f"[STEER] Center = {_calibrated_angle:.1f} degrees")
    else:
        _calibrated_angle = 0.0
        speak("Could not calibrate. Using default.")

def run():
    import cv2
    import numpy as np
    from modules.speaker    import speak
    from pipeline.hand_tracker    import HandTracker
    from pipeline.gesture_engine  import GestureEngine
    from gaming_mode.copilot      import RacingCopilot

    # Launch Asphalt
    speak("Launching Asphalt 9 Sir.")
    if os.path.exists(ASPHALT_EXE):
        subprocess.Popen([ASPHALT_EXE], cwd=os.path.dirname(ASPHALT_EXE))
    else:
        speak("Asphalt not found. Open it manually Sir.")

    # Wait for game
    speak("Waiting for game to load Sir.")
    for _ in range(30):
        try:
            import pygetwindow as gw
            for win in gw.getAllWindows():
                if "asphalt" in win.title.lower():
                    speak("Game ready Sir.")
                    focus_game()
                    time.sleep(1)
                    break
        except: pass
        time.sleep(2)

    # Camera init
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS,          60)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    tracker  = HandTracker()
    gesture_e= GestureEngine()
    copilot  = RacingCopilot()

    # HUD window — top right
    cv2.namedWindow("ULTRON HUD", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("ULTRON HUD", w, h)
    cv2.setWindowProperty("ULTRON HUD", cv2.WND_PROP_TOPMOST, 1)
    cv2.moveWindow("ULTRON HUD", 1920-w-10, 10)

    # Calibrate
    calibrate(cap, tracker)

    speed       = 0
    fps_time    = time.time()
    fps         = 0
    frame_count = 0
    last_focus  = time.time()
    game_state  = "idle"
    prev_gesture= set()

    speak("Gaming mode active Sir. Use both hands to steer. Fist to accelerate.")

    while True:
        ret, frame = cap.read()
        if not ret: time.sleep(0.01); continue
        frame = cv2.flip(frame, 1)

        # Brightness
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg  = float(np.mean(gray))
        if avg < 85:   frame = cv2.convertScaleAbs(frame, alpha=min(110/max(avg,1),2.2), beta=8)
        elif avg > 155:frame = cv2.convertScaleAbs(frame, alpha=max(105/avg,0.45))

        # Track
        hands_data = tracker.process(frame)
        all_gestures= []
        for hand in hands_data:
            g = gesture_e.recognize(hand)
            all_gestures.extend(g)
        gesture_names = set(g["name"] for g in all_gestures)

        # Steering
        steer       = get_steering(hands_data)
        wheel_angle = steer * 45.0
        apply_steering(steer)

        # Gestures → game actions
        if "fist" in gesture_names:
            _press('w'); _release('s')
            game_state = "accel"
        elif "open_palm" in gesture_names:
            _press('s'); _release('w')
            game_state = "brake"
        elif "point" in gesture_names and "point" not in prev_gesture:
            if USE_PYNPUT:
                _kb.press(' '); time.sleep(0.05); _kb.release(' ')
            game_state = "nitro"
        elif "pinch" in gesture_names:
            _press('shift')
            game_state = "idle"
        else:
            _release('w'); _release('s'); _release('shift')
            game_state = "idle"

        prev_gesture = gesture_names.copy()

        # Speed simulation
        if 'w' in _prev_keys:    speed = min(speed+3, 220)
        elif 's' in _prev_keys:  speed = max(speed-9, 0)
        elif speed > 0:          speed = max(speed-2, 0)

        # Refocus game every 8s
        now = time.time()
        if now - last_focus > 8:
            last_focus = now
            focus_game()
            time.sleep(0.05)
            cv2.setWindowProperty("ULTRON HUD", cv2.WND_PROP_TOPMOST, 1)

        # Co-pilot
        status = {"steering":steer,"keys_pressed":list(_prev_keys),"action":game_state}
        copilot.analyze(status, speed, len(hands_data)>0)

        # Draw wheel between hands
        if len(hands_data) >= 2:
            sh   = sorted(hands_data, key=lambda h: h['palm'][0])
            lh,rh= sh[0], sh[1]
            wcx  = int((lh['palm'][0]+rh['palm'][0])/2)
            wcy  = int((lh['palm'][1]+rh['palm'][1])/2)
            dist = math.sqrt((rh['palm'][0]-lh['palm'][0])**2+(rh['palm'][1]-lh['palm'][1])**2)
            wrad = max(30, min(80, int(dist*0.4)))
        elif len(hands_data) == 1:
            wcx,wcy,wrad = int(hands_data[0]['palm'][0]),int(hands_data[0]['palm'][1]),45
        else:
            wcx,wcy,wrad = w//2, h//2, 50

        draw_wheel(frame, wcx, wcy, wrad, wheel_angle, steer, game_state)
        tracker.draw(frame, hands_data)

        # HUD info
        frame_count += 1
        if time.time()-fps_time >= 1.0:
            fps=frame_count; frame_count=0; fps_time=time.time()

        cv2.rectangle(frame,(0,0),(w,26),(8,6,4),-1)
        cv2.putText(frame, f"FPS:{fps} HANDS:{len(hands_data)} STEER:{steer:+.2f}",
                   (4,18), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0,210,230), 1)
        cv2.putText(frame, f"{speed} KM/H",
                   (w-70,50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,210,230), 2)
        cv2.putText(frame, "Q=QUIT | C=RECALIBRATE",
                   (4, h-6), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (80,80,80), 1)

        cv2.imshow("ULTRON HUD", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            speak("Exiting gaming mode Sir.")
            break
        elif key == ord('c'):
            calibrate(cap, tracker)

    _release_all()
    tracker.release()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run()