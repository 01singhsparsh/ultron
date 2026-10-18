import subprocess, threading, queue

_q              = queue.Queue()
_worker_started = False

def _worker():
    while True:
        try:
            text = _q.get(timeout=1)
            if not text: continue
            clean = text.replace("'","").replace('"',"").replace('\n',' ').strip()
            if not clean: continue
            try:
                from hud.hud_manager import set_speaking
                set_speaking(True)
            except: pass
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate',   185)
                engine.setProperty('volume', 1.0)
                voices = engine.getProperty('voices')
                for v in voices:
                    if 'zira' in v.name.lower() or 'david' in v.name.lower():
                        engine.setProperty('voice', v.id)
                        break
                engine.say(clean)
                engine.runAndWait()
                engine.stop()
                del engine
            except Exception as e:
                print(f"[SPEAKER] pyttsx3 error: {e}")
                try:
                    cmd = (
                        f'Add-Type -AssemblyName System.Speech;'
                        f'$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;'
                        f'$s.Rate=2;$s.Volume=100;$s.Speak("{clean}")'
                    )
                    subprocess.call(
                        ['powershell','-WindowStyle','Hidden','-NonInteractive','-Command',cmd],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except Exception as e2:
                    print(f"[SPEAKER] Fallback error: {e2}")
            try:
                from hud.hud_manager import set_speaking
                set_speaking(False)
            except: pass
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[SPEAKER] Worker error: {e}")

def _ensure_worker():
    global _worker_started
    if not _worker_started:
        _worker_started = True
        t = threading.Thread(target=_worker, daemon=True)
        t.name = "SpeakerWorker"
        t.start()

def speak(text: str):
    if not text or not text.strip(): return
    print(f"  ULTRON: {text}")
    try:
        from hud.hud_manager import set_response
        set_response(text)
    except: pass
    _ensure_worker()
    while not _q.empty():
        try: _q.get_nowait()
        except: break
    _q.put(text)

def stop_speaking():
    while not _q.empty():
        try: _q.get_nowait()
        except: break