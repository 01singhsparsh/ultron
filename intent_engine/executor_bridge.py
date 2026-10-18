"""
executor_bridge.py
Bridges intent plans to actual executors.
Every action is real â€” never hallucinated.
"""
import os, sys, time
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR,"config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass
    if not GROQ_API_KEY:
        GROQ_API_KEY = __import__("os").environ.get("GROQ_API_KEY", "")

_load_key()

def _speak(text):
    try:
        from modules.speaker import speak
        speak(text)
    except: print(f"[BRIDGE] {text}")

def _listen(timeout=6):
    try:
        from modules.listener import listen
        return listen(timeout=timeout, phrase_limit=10)
    except: return None

def _groq(prompt, system=None, max_tokens=80):
    if not GROQ_API_KEY: return ""
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        msgs   = []
        if system: msgs.append({"role":"system","content":system})
        msgs.append({"role":"user","content":prompt})
        r = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=msgs, max_tokens=max_tokens, temperature=0.5)
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"[BRIDGE] Groq error: {e}")
        return ""

def execute_plan(steps: list, raw_text: str = "") -> dict:
    result  = {"success":True,"response":"","steps_done":0}
    context = {"raw":raw_text}

    for step in steps:
        action = step.get("action","")
        params = step.get("params",{})
        params["raw"] = raw_text

        print(f"[BRIDGE] Executing: {action}")
        step_result = _execute_step(action, params, context)

        if step_result.get("response"):
            result["response"] = step_result["response"]

        if not step_result.get("success",True):
            fallback = step.get("on_fail")
            if fallback: _execute_step(fallback, params, context)
            else: result["success"] = False; break

        if action == "check_app_running" and step_result.get("is_running"):
            _execute_step("focus_app", params, context)
            break

        context.update(step_result.get("context_update",{}))
        result["steps_done"] += 1

    return result

def _execute_step(action: str, params: dict, context: dict) -> dict:
    try:
        # â”€â”€ App actions â”€â”€
        if action == "launch_app":
            from executor.app_launcher import launch_app
            r = launch_app(params.get("app",""))
            _speak(r["message"])
            return {"success":r["success"],"response":r["message"]}

        elif action == "check_app_running":
            from executor.app_launcher import is_app_running
            app     = params.get("app","").lower()
            running = is_app_running(app)
            return {"success":True,"is_running":running}

        elif action == "focus_app":
            from executor.window_manager import focus_window
            r = focus_window(params.get("app",""))
            _speak(r["message"])
            return {"success":r["success"],"response":r["message"]}

        elif action == "close_app":
            from executor.app_launcher import close_app
            r = close_app(params.get("app",""))
            return {"success":r["success"],"response":r["message"]}

        elif action == "verify_app_open":
            time.sleep(1.5)
            from executor.app_launcher import is_app_running
            app = params.get("app","").lower()
            return {"success":is_app_running(app)}

        # â”€â”€ Website actions â”€â”€
        elif action == "open_website":
            from executor.website_launcher import open_website
            site = params.get("site","")
            r    = open_website(site)
            _speak(r["message"])
            return {"success":r["success"],"response":r["message"]}

        elif action == "check_website_open":
            from executor.screen_context import get_open_apps
            site  = params.get("site","").lower()
            apps  = get_open_apps()
            found = any(site in a.lower() for a in apps)
            return {"success":True,"is_open":found}

        # â”€â”€ Window actions â”€â”€
        elif action == "window_action":
            from executor.window_manager import execute_window_action
            r = execute_window_action(params.get("action","focus"),
                                     params.get("target",""))
            return {"success":r["success"],"response":r["message"]}

        # â”€â”€ Screen context â”€â”€
        elif action == "get_screen_context":
            from executor.screen_context import describe_screen
            desc = describe_screen()
            _speak(f"Sir, {desc}")
            return {"success":True,"response":desc}

        # â”€â”€ WhatsApp â”€â”€
        elif action == "open_platform":
            platform = params.get("platform","whatsapp")
            if "whatsapp" in platform:
                import subprocess
                # Try WhatsApp Beta first
                try:
                    subprocess.Popen(
                        ['powershell','-Command',
                         'start-process "shell:AppsFolder\5319275A.WhatsAppBeta_cv1g1gvanyjgm!WhatsAppBeta"'],
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                except:
                    try:
                        subprocess.Popen(
                            ['powershell','-Command','start-process whatsapp:'],
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    except: pass
                time.sleep(5)
            return {"success":True}

        elif action == "search_contact":
            import pyautogui
            contact = params.get("contact","")
            try:
                import pygetwindow as gw
                for win in gw.getAllWindows():
                    if 'whatsapp' in win.title.lower():
                        win.activate(); break
            except: pass
            time.sleep(0.5)
            pyautogui.hotkey('ctrl','f')
            time.sleep(0.8)
            pyautogui.hotkey('ctrl','a')
            pyautogui.typewrite(contact, interval=0.05)
            time.sleep(1.5)
            pyautogui.press('enter')
            time.sleep(0.8)
            return {"success":True}

        elif action == "confirm_send":
            contact = params.get("contact","")
            message = params.get("message","")
            _speak(f"Sir, sending '{message}' to {contact}. Confirm?")
            resp = _listen(timeout=5)
            confirmed = resp and any(w in resp.lower() for w in ["yes","send","okay","sure","haan"])
            return {"success":confirmed,"confirmed":confirmed}

        elif action == "type_message":
            import pyautogui
            screen_w,screen_h = pyautogui.size()
            pyautogui.click(screen_w//2, int(screen_h*0.93))
            time.sleep(0.4)
            pyautogui.typewrite(params.get("message",""), interval=0.04)
            return {"success":True}

        elif action == "send_message":
            import pyautogui
            pyautogui.press('enter')
            time.sleep(0.3)
            return {"success":True}

        # â”€â”€ System info â”€â”€
        elif action == "get_system_info":
            import psutil, datetime
            batt = psutil.sensors_battery()
            cpu  = psutil.cpu_percent(interval=1)
            ram  = psutil.virtual_memory().percent
            info = f"CPU at {int(cpu)} percent. RAM at {int(ram)} percent."
            if batt: info += f" Battery at {int(batt.percent)} percent."
            _speak(info)
            return {"success":True,"response":info}

        # â”€â”€ Session restore â”€â”€
        elif action == "load_last_session":
            from context_engine.session_manager import get_last_session
            session = get_last_session(params.get("time_ref","yesterday"))
            return {"success":True,"context_update":{"session":session}}

        elif action == "restore_workspace":
            from context_engine.workspace_manager import restore_workspace
            session = context.get("session",{})
            restore_workspace(session)
            return {"success":True}

        elif action == "summarize_session":
            from context_engine.session_manager import summarize_session
            session = context.get("session",{})
            summary = summarize_session(session)
            _speak(summary)
            return {"success":True,"response":summary}

        # â”€â”€ Gaming â”€â”€
        elif action == "start_gaming_mode":
            from gaming_mode.gaming_mode import start_gaming_mode
            _speak("Activating Gaming Mode Sir.")
            start_gaming_mode(params.get("game",""))
            return {"success":True,"response":"Gaming mode activated."}

        # â”€â”€ LLM fallback â”€â”€
        elif action == "llm_answer":
            from smart_brain import smart_answer
            query = params.get("query","") or params.get("raw","")
            if query:
                answer = smart_answer(query)
                _speak(answer)
                return {"success":True,"response":answer}
            return {"success":False}

        # â”€â”€ Speak â”€â”€
        elif action == "speak":
            _speak(params.get("text",""))
            return {"success":True}

        # â”€â”€ Ask user â”€â”€
        elif action == "ask_user":
            _speak(params.get("question",""))
            resp = _listen(timeout=6)
            return {"success":True,"user_response":resp or ""}

        else:
            print(f"[BRIDGE] Unknown action: {action}")
            return {"success":True}

    except Exception as e:
        print(f"[BRIDGE] Step error ({action}): {e}")
        return {"success":False,"error":str(e)}


