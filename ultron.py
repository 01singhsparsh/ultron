import sys, os, time, datetime, threading, re, json
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
SIGNAL_FILE = os.path.join(BASE_DIR, "data", "wake_signal.txt")
HUD_FILE    = os.path.join(BASE_DIR, "data", "hud_state.json")
sys.path.insert(0, BASE_DIR)
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
 
from modules.speaker  import speak
from modules.listener import listen
from modules.commands import handle_command
from smart_brain      import smart_answer, handle_memory_command
from proactive        import start_proactive
from mood             import detect_mood, get_mood_response_prefix
 
try:
    from hands_free.voice_integration import handle_hands_free_command
    _HANDS_FREE_AVAILABLE = True
    print("[ULTRON] Hands-Free Mode: LOADED")
except ImportError:
    _HANDS_FREE_AVAILABLE = False
    def handle_hands_free_command(text): return False
    print("[ULTRON] Hands-Free Mode: NOT INSTALLED")
 
WAKE_WORDS  = ["ultron","hey ultron","hello ultron","hello","activate"]
SLEEP_WORDS = ["sleep","stop","bye","goodbye","exit"]
 
AGENT_TRIGGERS = [
    r'create a folder',r'make a folder',r'new folder',
    r'create a file',r'make a file',
    r'install\s+\w',r'download and install',
    r'go to desktop',r'show desktop',
    r'move .+ to recycle bin',r'organize my downloads',
    r'delete the folder',r'delete the file',
    r'move the file',r'copy the file',r'create a project',
]
 
MULTI_AGENT_TRIGGERS = [
    r'write (a |an )?(python |code |script )',
    r'create (a |an )?(app|script|program|tool)',
    r'build (a |an )?',r'fix (the |this |my )?error',
    r'debug',r'research .+ and',
    r'what should i (study|learn)',r'plan my',
    r'help me (understand|learn|build|create)',
]
 
PLAY_PATTERNS = [
    r'^play\s+(.+)',
    r'^chalao\s+(.+)',
    r'^gana\s+(?:bajao|chalao?)\s+(.+)',
    r'^(.+)\s+(?:song|gana|music)\s+(?:play|bajao|chalao?)',
    r'^youtube\s+pe\s+(.+)\s+(?:play|search|chalao)',
]
 
def _needs_agent(t):
    return any(re.search(p,t.lower()) for p in AGENT_TRIGGERS)
 
def _needs_multi_agent(t):
    return any(re.search(p,t.lower()) for p in MULTI_AGENT_TRIGGERS)
 
def _is_play_command(text: str):
    t = text.lower().strip()
    for pattern in PLAY_PATTERNS:
        m = re.match(pattern, t)
        if m:
            query = m.group(1).strip()
            for filler in ["please","sir","yaar","bhai","zara","ek","baar"]:
                query = query.replace(filler,"").strip()
            if query and len(query) > 1:
                return query
    return None
 
def _write_hud(data: dict):
    try:
        with open(HUD_FILE,'w') as f: json.dump(data,f)
    except: pass
 
def _hud(state: str):         _write_hud({"state":state})
def _hud_heard(text: str):    _write_hud({"heard":text})
def _hud_response(text: str): _write_hud({"response":text[:80]})
 
def _hud_notify(text: str):
    try:
        from hud.hud_manager import notify
        notify(text[:38])
    except: pass
 
def is_wake(t):
    if not t: return False
    return any(w in t.lower().strip() for w in WAKE_WORDS)
 
def is_sleep(t):
    if not t: return False
    return any(w in t.lower() for w in SLEEP_WORDS)
 
def _translate_to_english(text: str) -> str:
    has_hindi    = any('\u0900' <= c <= '\u097F' for c in text)
    hinglish     = ['karo','karna','khol','band','bhej','bata','batao','bol',
                    'mujhe','mera','meri','yaar','bhai','aur','hai','nahi',
                    'haan','theek','accha','suno','dekho','jao','aao','chal',
                    'chalo','kya','kaun','kab','kahan','kyun','kaise','kitna',
                    'chalao','bajao','gana','sunao','dikha','lao']
    has_hinglish = any(w in text.lower().split() for w in hinglish)
    if not has_hindi and not has_hinglish: return text
    try:
        GROQ_API_KEY = __import__("os").environ.get("GROQ_API_KEY", "")
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        r = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {"role":"system","content":"Translate Hindi/Hinglish to English. Return ONLY the translation, nothing else."},
                {"role":"user",  "content":f"Translate: {text}"}
            ],
            max_tokens=80, temperature=0.1
        )
        translated = r.choices[0].message.content.strip()
        print(f"[TRANSLATE] '{text}' -> '{translated}'")
        return translated
    except Exception as e:
        print(f"[TRANSLATE] Error: {e}")
        return text
 
def _smart_open(text: str) -> bool:
    import webbrowser, subprocess
    t = text.lower().strip()
    open_match = re.search(r'^(?:open|launch|start|khol|chalu|shuru)\s+(.+)',t)
    if not open_match: return False
    target = open_match.group(1).strip()
    APP_MAP = {
        "whatsapp":      "WhatsAppBeta",
        "whatsapp beta": "WhatsAppBeta",
        "brave":         "brave",
        "chrome":        "chrome",
        "google chrome": "chrome",
        "spotify":       "Spotify",
        "discord":       "Discord",
        "vs code":       "code",
        "vscode":        "code",
        "notepad":       "notepad",
        "calculator":    "calc",
        "telegram":      "Telegram",
        "vlc":           "vlc",
        "zoom":          "Zoom",
        "word":          "WINWORD",
        "excel":         "EXCEL",
        "powerpoint":    "POWERPNT",
    }
    for key, exe in APP_MAP.items():
        if key in target:
            try:
                from executor.app_launcher import is_app_running, launch_app
                from executor.window_manager import focus_window
                if is_app_running(exe):
                    focus_window(key)
                    speak(f"{key.title()} is already open Sir.")
                    return True
                result = launch_app(key)
                speak(result["message"])
                return True
            except Exception as e:
                print(f"[SMART_OPEN] App error: {e}")
    SITE_MAP = {
        "chatgpt":      "https://chatgpt.com",
        "claude":       "https://claude.ai",
        "github":       "https://github.com",
        "linkedin":     "https://linkedin.com",
        "gmail":        "https://mail.google.com",
        "google drive": "https://drive.google.com",
        "instagram":    "https://instagram.com",
        "twitter":      "https://twitter.com",
        "netflix":      "https://netflix.com",
        "amazon":       "https://amazon.in",
        "youtube":      "https://youtube.com",
        "google":       "https://google.com",
        "reddit":       "https://reddit.com",
        "stackoverflow":"https://stackoverflow.com",
        "notion":       "https://notion.so",
        "figma":        "https://figma.com",
        "canva":        "https://canva.com",
        "colab":        "https://colab.research.google.com",
        "huggingface":  "https://huggingface.co",
    }
    for key, url in SITE_MAP.items():
        if key in target:
            speak(f"Opening {key.title()} Sir.")
            webbrowser.open(url)
            return True
    if re.search(r'\.(com|in|org|io|net|co)\b', target):
        url = target if target.startswith("http") else f"https://{target}"
        speak(f"Opening {target} Sir.")
        webbrowser.open(url)
        return True
    return False
 
def _play_on_youtube(query: str):
    import webbrowser
    speak(f"Playing {query} on YouTube Sir.")
    url = f"https://www.youtube.com/results?search_query={query.replace(' ','+')}"
    webbrowser.open(url)
    def _auto_click():
        time.sleep(6)
        try:
            import pygetwindow as gw, pyautogui
            for win in gw.getAllWindows():
                if "youtube" in win.title.lower():
                    win.activate(); break
            time.sleep(1)
            for _ in range(4):
                pyautogui.press('tab')
                time.sleep(0.15)
            pyautogui.press('enter')
        except Exception as e:
            print(f"[PLAY] Auto-click error: {e}")
    threading.Thread(target=_auto_click, daemon=True).start()
 
def greet_on_start():
    try:
        from memory.personality import get_greeting
        speak(get_greeting())
    except:
        hour = datetime.datetime.now().hour
        if hour < 12:   g = "Good morning"
        elif hour < 17: g = "Good afternoon"
        else:           g = "Good evening"
        speak(f"{g} Sir. Ultron online. All systems ready.")
 
def active_mode():
    print("\nULTRON ACTIVE - Listening...\n")
    _hud("LISTENING")
    time.sleep(0.3)
    speak("Always for you Sparsh Sir. How can I assist you?")
    _hud_response("Always for you Sparsh Sir.")
    time.sleep(2.5)
    _hud("ONLINE")
 
    while True:
        text = listen(timeout=4, phrase_limit=6)
        if not text: continue
        print(f"You said: {text}")
        # ── INSTANT VOICE CLICK ──
        _click_words = ["click","tap","press","click here","click karo","kar click","left click","yahan click","do click"]
        if text.lower().strip() in _click_words:
            if _HANDS_FREE_AVAILABLE:
                try:
                    from hands_free.hands_free_manager import HandsFreeManager as _HFM
                    _hfm = _HFM.get_instance()
                    if _hfm.is_active:
                        import pyautogui as _pag
                        _pag.click()
                        print("[HANDS-FREE] VOICE CLICK FIRED")
                        speak("Click Sir.")
                        _hud("ONLINE"); continue
                except Exception as _ce:
                    print(f"[CLICK ERROR] {_ce}")

        _hud_heard(f"â–º {text}")
 
        if is_sleep(text):
            speak("Going to sleep Sir. Say Ultron anytime.")
            _hud("ONLINE"); return
 
        mood = detect_mood(text)
        if mood == "stressed":
            speak("Take a breath Sir. I am here to help.")
 
        _hud("THINKING")
 
        # Translate Hindi/Hinglish
        english_text = _translate_to_english(text)
        if english_text != text:
            print(f"[ULTRON] Translated: {english_text}")
 
 
        if _HANDS_FREE_AVAILABLE:
            try:
                if handle_hands_free_command(english_text):
                    _hud("ONLINE"); continue
            except Exception as _hfe:
                print(f"[HANDS-FREE] {_hfe}")
 
        try:
            from earth_mode.earth_mode import handle_earth_command
            if handle_earth_command(english_text):
                _hud("ONLINE"); continue
        except Exception as e:
            print(f"[EARTH] {e}")
 
        mem_reply = handle_memory_command(english_text)
        if mem_reply:
            speak(mem_reply); _hud_response(mem_reply)
            try:
                from memory.episodic_memory import save_exchange
                save_exchange(text, mem_reply)
            except: pass
            _hud("ONLINE"); continue
 
        play_query = _is_play_command(english_text)
        if play_query:
            _play_on_youtube(play_query)
            _hud("ONLINE"); continue
 
        if re.match(r'^(open|launch|start|khol)\s+', english_text.lower()):
            if _smart_open(english_text):
                _hud("ONLINE"); continue
 
        t_lower = english_text.lower()
        if any(p in t_lower for p in ["open chat","open chats","chats of","chat of"]):
            try:
                from modules.commands import whatsapp_open_chat
                whatsapp_open_chat(english_text)
                _hud("ONLINE"); continue
            except Exception as e:
                print(f"[WA] {e}")
 
        if any(p in t_lower for p in ["send","message to","bhej","ko message","whatsapp"]):
            if any(name_hint in t_lower for name_hint in ["to ","ko ","her ","him "]):
                try:
                    from modules.commands import whatsapp_full_flow
                    whatsapp_full_flow(english_text)
                    _hud("ONLINE"); continue
                except Exception as e:
                    print(f"[WA] {e}")
 
        try:
            from hud.app_launcher_hud import voice_launch
            if voice_launch(english_text):
                speak("Opening it now Sir.")
                _hud("ONLINE"); continue
        except: pass
 
        try:
            from intent_engine.resolver import resolve, should_use_intent_engine
            if should_use_intent_engine(english_text):
                result = resolve(english_text)
                if result.get("handled"):
                    response = result.get("response","")
                    if response:
                        speak(response); _hud_response(response)
                        try:
                            from memory.episodic_memory import save_exchange
                            save_exchange(text, response)
                        except: pass
                    _hud("ONLINE"); continue
        except Exception as e:
            print(f"[INTENT] {e}")
 
        try:
            from executor.command_router import classify_and_execute
            exec_result = classify_and_execute(english_text)
            if exec_result.get("handled"):
                response = exec_result.get("response","Done Sir.")
                speak(response); _hud_response(response)
                try:
                    from memory.episodic_memory import save_exchange
                    save_exchange(text, response)
                except: pass
                _hud("ONLINE"); continue
        except Exception as e:
            print(f"[EXECUTOR] {e}")
 
        # 10 â€” Direct commands
        if handle_command(english_text):
            _hud("ONLINE"); continue
 
        # 11 â€” Multi-Agent
        if _needs_multi_agent(english_text):
            speak("Activating multi-agent system Sir.")
            def _run_multi(t):
                try:
                    from multi_agent.orchestrator import run_multi_agent
                    result = run_multi_agent(t)
                    speak(result[:300] if len(result)>300 else result)
                    _hud_response(result[:80])
                except Exception as e:
                    speak(f"Error Sir: {str(e)[:80]}")
                _hud("ONLINE")
            threading.Thread(target=_run_multi, args=(english_text,), daemon=True).start()
            continue
 
        # 12 â€” Desktop Agent
        if _needs_agent(english_text):
            speak("On it Sir.")
            from agents.desktop_agent import run_agent
            threading.Thread(target=run_agent, args=(english_text,), daemon=True).start()
            _hud("ONLINE"); continue
 
        # 13 â€” Smart AI (last resort)
        speak("On it Sir.")
        reply  = smart_answer(english_text)
        prefix = get_mood_response_prefix()
        final  = prefix + reply if prefix and mood in ["stressed","tired"] else reply
        speak(final); _hud_response(final)
        try:
            from memory.episodic_memory import save_exchange
            save_exchange(text, reply, mood)
        except: pass
        _hud("ONLINE")
 
def idle_mode():
    print("ULTRON idle â€” Watching for voice or widget click...")
    last_face = 0
    try:
        from modules.face_auth import detect_my_face, is_face_registered
        face_ok = True
    except: face_ok = False
 
    while True:
        now = time.time()
        if os.path.exists(SIGNAL_FILE):
            try:
                os.remove(SIGNAL_FILE)
                print("[ULTRON] Widget clicked!")
                _hud("LISTENING"); return
            except: pass
        if face_ok and now - last_face > 8:
            last_face = now
            try:
                if is_face_registered() and detect_my_face(timeout=3):
                    print("Face recognized!"); return
            except: pass
        text = listen(timeout=3, phrase_limit=3)
        if text: print(f"Heard: {text}")
        if is_wake(text): return
        time.sleep(0.05)
 
def _wait_for_internet(max_wait=30):
    import socket
    print("[ULTRON] Checking internet connection...")
    for i in range(max_wait):
        try:
            socket.setdefaulttimeout(2)
            socket.create_connection(("8.8.8.8", 53))
            print("[ULTRON] Internet ready.")
            return True
        except OSError:
            if i == 0:
                print("[ULTRON] Waiting for internet...")
            time.sleep(1)
    print("[ULTRON] No internet â€” running in offline mode.")
    return False
 
_wait_for_internet(20)
 
start_proactive()
try:
    from context_engine.session_manager import start_recording
    start_recording()
except: pass
 
greet_on_start()
 
while True:
    try:
        idle_mode()
        active_mode()
    except KeyboardInterrupt:
        speak("Goodbye Sparsh Sir.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
 




