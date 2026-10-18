import threading, time, sys, os, subprocess
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

_process   = None
_running   = False
_chat_file = os.path.join(BASE_DIR, "data", "pipeline_chat.json")

def start_pipeline():
    global _process, _running
    if _running: return
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

    # Write launcher script
    launcher = os.path.join(BASE_DIR, "pipeline", "pipeline_launcher.py")
    _write_launcher(launcher)

    try:
        _process = subprocess.Popen(
            ["py", "-3.11", launcher],
            cwd=BASE_DIR,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        _running = True
        print("[PIPELINE] Started in separate process")
        threading.Thread(target=_monitor, daemon=True).start()
    except Exception as e:
        print(f"[PIPELINE] Launch error: {e}")
        _running = False

def _write_launcher(path):
    code = '''
import sys, os
sys.path.insert(0, r"''' + BASE_DIR + r'''")

import cv2
import numpy as np
import time
import json

from pipeline.hand_tracker   import HandTracker
from pipeline.gesture_engine import GestureEngine
from pipeline.renderer       import HolographicRenderer
from pipeline.workspace      import Workspace

CHAT_FILE = r"''' + _chat_file + r'''"

def run():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    tracker   = HandTracker()
    gesture_e = GestureEngine()
    renderer  = HolographicRenderer(w, h)
    workspace = Workspace(w, h)
    workspace.spawn_default_panels()

    prev_fist    = False
    fps_time     = time.time()
    fps          = 0
    frame_count  = 0
    pinch_was_on = False

    cv2.namedWindow("ULTRON PIPELINE", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("ULTRON PIPELINE", w, h)

    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)

        # Software brightness correction
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg  = np.mean(gray)
        if avg < 90:
            factor = min(110 / max(avg, 1), 2.5)
            frame  = cv2.convertScaleAbs(frame, alpha=factor, beta=10)
        elif avg > 150:
            factor = max(110 / avg, 0.4)
            frame  = cv2.convertScaleAbs(frame, alpha=factor, beta=0)

        hands_data   = tracker.process(frame)
        all_gestures = []
        pinching_hands = set()

        for idx, hand in enumerate(hands_data):
            g = gesture_e.recognize(hand)
            all_gestures.extend(g)
            if any(x["name"] == "pinch" for x in g):
                pinching_hands.add(idx)

        if len(hands_data) >= 2:
            tg = gesture_e.recognize_two_hands(hands_data)
            all_gestures.extend(tg)

        gesture_names = [g["name"] for g in all_gestures]
        pinch_events  = [g for g in all_gestures if g["name"] == "pinch"]
        pinch_now     = len(pinch_events) > 0

        if pinch_now:
            g = pinch_events[0]
            px, py       = g["position"]
            just_started = not pinch_was_on
            if workspace.draw_mode:
                if just_started: workspace.current_stroke = [(int(px), int(py))]
                else:            workspace.current_stroke.append((int(px), int(py)))
            else:
                workspace.handle_pinch(px, py, just_started)
        else:
            if pinch_was_on:
                if workspace.draw_mode and len(workspace.current_stroke) > 1:
                    workspace.strokes.append(workspace.current_stroke.copy())
                workspace.current_stroke = []
                workspace.handle_pinch_end()
        pinch_was_on = pinch_now

        if "two_hand_pinch" in gesture_names:
            for g in all_gestures:
                if g["name"] == "two_hand_pinch":
                    workspace.handle_scale(g["scale_distance"])

        is_fist = "fist" in gesture_names
        if is_fist and not prev_fist:
            fist_g = next((g for g in all_gestures if g["name"] == "fist"), None)
            if fist_g:
                name, obj = workspace.physics.get_object_at(*fist_g["position"])
                if name: workspace.close_panel(name)
        prev_fist = is_fist

        if "swipe_right" in gesture_names:
            workspace.spawn_panel(f"panel_{int(time.time())}", "NEW PANEL", x=50, y=100, w=300, h=200)

        # Read chat updates from file
        try:
            if os.path.exists(CHAT_FILE):
                with open(CHAT_FILE) as f:
                    data = json.load(f)
                if data.get("new"):
                    workspace.update_chat_panel(data.get("query",""), data.get("response",""))
                    data["new"] = False
                    with open(CHAT_FILE,"w") as f: json.dump(data, f)
        except: pass

        workspace.update()
        tracker.draw(frame, hands_data)

        # Debug info
        if hands_data:
            hd  = hands_data[0]
            pd  = gesture_e._pinch_distance(hd["landmarks"])
            th  = max(25, min(60, hd["hand_size"] * 0.30))
            col = (0,255,0) if pd < th else (0,100,255)
            cv2.putText(frame, f"PINCH:{int(pd)}/{int(th)}  MODE:{'DRAW' if workspace.draw_mode else 'GRAB'}",
                       (10,55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1)
            cv2.putText(frame, f"GESTURES:{gesture_names[:3]}",
                       (10,75), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,230,210), 1)

        frame = renderer.render(frame, workspace.panels, hands_data, all_gestures,
                               workspace.strokes, workspace.current_stroke,
                               workspace.draw_mode, pinching_hands)

        frame_count += 1
        if time.time() - fps_time >= 1.0:
            fps = frame_count; frame_count = 0; fps_time = time.time()
        cv2.putText(frame, f"FPS:{fps}", (w-70,24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,230,210), 1)

        cv2.imshow("ULTRON PIPELINE", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"): break
        elif key == ord("d"):
            m = workspace.toggle_draw_mode()
            print(f"[PIPELINE] Draw mode: {m}")
        elif key == ord("c"):
            workspace.clear_drawing()

    tracker.release()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run()
'''
    with open(path, 'w') as f:
        f.write(code)

def _monitor():
    global _running, _process
    if _process:
        _process.wait()
        _running = False
        print("[PIPELINE] Process ended")

def stop_pipeline():
    global _process, _running
    _running = False
    if _process:
        try: _process.terminate()
        except: pass
        _process = None

def pipeline_update_chat(query, response):
    try:
        import json
        os.makedirs(os.path.dirname(_chat_file), exist_ok=True)
        with open(_chat_file, 'w') as f:
            json.dump({"new": True, "query": query, "response": response}, f)
    except: pass

def is_running():
    return _running