import os, sys, time, re, pyautogui, threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from agents.task_planner   import plan_task, is_complex_task
from agents.app_controller import open_app, close_app, focus_app, install_software
from agents.browser_agent  import open_url, search_web, download_file
from agents.file_agent     import (create_file, read_file, delete_file,
                                    create_folder, create_folder_on_desktop,
                                    list_files, copy_file, move_file,
                                    find_file, run_command, organize_downloads)
from modules.speaker import speak

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.3

DESKTOP   = os.path.join(os.path.expanduser("~"), "Desktop")
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
DOCUMENTS = os.path.join(os.path.expanduser("~"), "Documents")

def _extract_folder_name(text):
    t = text.lower()
    patterns = [
        r'(?:folder|directory)\s+(?:called|named|with name)\s+["\']?([^"\']+?)["\']?\s+(?:on|in|at)',
        r'(?:folder|directory)\s+(?:called|named|with name)\s+["\']?([^"\']+?)["\']?$',
        r'(?:create|make|new)\s+(?:a\s+)?(?:folder|directory)\s+["\']?([^"\']+?)["\']?\s+(?:on|in|at)',
        r'["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            name = match.group(1).strip()
            name = re.sub(r'\s*(on|in|at)\s*(desktop|downloads|documents).*$','',name).strip()
            if name: return name.title()
    return "New Folder"

def _extract_location(text):
    t = text.lower()
    if "desktop"   in t: return DESKTOP
    if "downloads" in t: return DOWNLOADS
    if "documents" in t: return DOCUMENTS
    return DESKTOP

class DesktopAgent:
    def __init__(self):
        self.task_history = []
        self.is_executing = False

    def _handle_directly(self, goal):
        t = goal.lower()

        # GO TO DESKTOP
        if re.search(r'go to desktop|show desktop|open desktop', t):
            import subprocess
            subprocess.Popen(f'explorer "{DESKTOP}"', shell=True)
            speak("Opening Desktop Sir."); return True

        # MOVE TO RECYCLE BIN
        if re.search(r'move .+ to (?:recycle bin|trash|bin)', t):
            import glob
            name_match = re.search(r'move (?:the )?(?:file |word file |pdf |document )?["\']?(.+?)["\']? to (?:recycle bin|trash|bin)', t)
            if name_match:
                name = name_match.group(1).strip()
                speak(f"Searching for {name} Sir.")
                found = []
                for d in [DESKTOP, DOWNLOADS, DOCUMENTS]:
                    found.extend(glob.glob(os.path.join(d, f"*{name}*")))
                if found:
                    import send2trash
                    for f in found: send2trash.send2trash(f)
                    speak(f"Done Sir. {os.path.basename(found[0])} moved to Recycle Bin.")
                else:
                    speak(f"Sir, could not find any file named {name}.")
            return True

        # CREATE FOLDER
        if re.search(r'create|make|new', t) and re.search(r'folder|directory', t):
            name     = _extract_folder_name(goal)
            location = _extract_location(goal)
            path     = os.path.join(location, name)
            speak(f"Creating folder {name} Sir.")
            success  = create_folder(path)
            if success:
                speak(f"Done Sir. Folder {name} created on {os.path.basename(location)}.")
                import subprocess
                subprocess.Popen(f'explorer "{path}"', shell=True)
            else:
                speak("Sorry Sir. Could not create the folder.")
            return True

        # CREATE FILE
        if re.search(r'create|make|new', t) and re.search(r'file|document|text file', t):
            name_match = re.search(r'(?:file|document)\s+(?:called|named)\s+["\']?([^"\']+?)["\']?\s*(?:on|in|$)', t)
            name       = name_match.group(1).strip() if name_match else "new_file.txt"
            location   = _extract_location(goal)
            path       = os.path.join(location, name)
            speak(f"Creating file {name} Sir.")
            success    = create_file(path, "")
            if success:
                speak(f"Done Sir. File {name} created.")
                import subprocess
                subprocess.Popen(["notepad", path])
            return True

        # ORGANIZE DOWNLOADS
        if re.search(r'organiz|sort|clean', t) and 'download' in t:
            speak("Organizing your Downloads folder Sir.")
            result = organize_downloads()
            if result: speak(f"Done Sir. I organized {len(result)} files into categories.")
            else:      speak("Downloads folder is already organized Sir.")
            return True

        # INSTALL SOFTWARE
        if re.search(r'^install\s+\w', t) or re.search(r'download and install', t):
            name_match = re.search(r'install\s+(.+?)(?:\s+on|\s+for|\s*$)', t)
            if name_match:
                name = name_match.group(1).strip()
                speak(f"Installing {name} Sir. This may take a few minutes.")
                threading.Thread(
                    target=lambda: (install_software(name), speak(f"{name} installation complete Sir.")),
                    daemon=True
                ).start()
            return True

        return False

    def execute_step(self, step):
        action = step.get("action","")
        params = step.get("params",{})
        desc   = step.get("description", action)
        print(f"[AGENT] Executing: {desc}")
        try:
            if action == "speak":             speak(params.get("text",""))
            elif action == "open_app":        open_app(params.get("app_name",""))
            elif action == "close_app":       close_app(params.get("app_name",""))
            elif action == "focus_app":       focus_app(params.get("app_name",""))
            elif action == "open_url":
                url = params.get("url","")
                if not url.startswith("http"): url = "https://" + url
                open_url(url)
            elif action == "search_web":      search_web(params.get("query",""))
            elif action == "type_text":       time.sleep(0.5); pyautogui.typewrite(params.get("text",""), interval=0.05)
            elif action == "press_key":
                key = params.get("key",""); keys = key.lower().split("+")
                if len(keys) > 1: pyautogui.hotkey(*keys)
                else: pyautogui.press(keys[0])
            elif action == "mouse_click":     pyautogui.click(params.get("x",0), params.get("y",0))
            elif action == "mouse_move":      pyautogui.moveTo(params.get("x",0), params.get("y",0), duration=0.5)
            elif action == "scroll":
                direction = params.get("direction","down"); amount = params.get("amount",3)
                pyautogui.scroll(amount if direction=="up" else -amount)
            elif action == "download_file":
                url  = params.get("url","")
                path = params.get("path", os.path.join(DOWNLOADS, url.split("/")[-1]))
                download_file(url, path)
            elif action == "run_command":     run_command(params.get("cmd",""))
            elif action == "create_file":     create_file(params.get("path",""), params.get("content",""))
            elif action == "read_file":
                content = read_file(params.get("path",""))
                if content: speak(f"File has {len(content)} characters Sir.")
            elif action == "delete_file":     delete_file(params.get("path",""))
            elif action == "create_folder":
                path = params.get("path","")
                path = path.replace("%USERPROFILE%", os.path.expanduser("~"))
                path = path.replace("~/Desktop", DESKTOP)
                if not os.path.isabs(path): path = os.path.join(DESKTOP, path)
                create_folder(path)
            elif action == "list_files":
                files = list_files(params.get("path","~"))
                speak(f"Found {len(files)} items Sir.")
            elif action == "copy_file":       copy_file(params.get("src",""), params.get("dst",""))
            elif action == "move_file":       move_file(params.get("src",""), params.get("dst",""))
            elif action == "install_software":
                name = params.get("name",""); speak(f"Installing {name} Sir.")
                install_software(name)
            elif action == "take_screenshot":
                path = os.path.join(DESKTOP, f"screenshot_{int(time.time())}.png")
                pyautogui.screenshot(path); speak("Screenshot saved Sir.")
            elif action == "wait":            time.sleep(params.get("seconds",1))
            else: print(f"[AGENT] Unknown action: {action}"); return False
            return True
        except Exception as e:
            print(f"[AGENT] Step error ({action}): {e}"); return False

    def execute_task(self, goal):
        if self.is_executing:
            speak("Sir I am already on a task. Please wait.")
            return False
        self.is_executing = True
        print(f"\n[AGENT] Task: {goal}")
        try:
            if self._handle_directly(goal): return True
            speak("Planning this Sir. One moment.")
            steps = plan_task(goal)
            if not steps: speak("Sorry Sir. Could not plan that task."); return False
            speak(f"Executing {len(steps)} steps Sir.")
            success_count = 0
            for i, step in enumerate(steps):
                print(f"[AGENT] Step {i+1}/{len(steps)}: {step.get('description','')}")
                if self.execute_step(step): success_count += 1
                time.sleep(0.3)
            self.task_history.append({"goal": goal, "steps": len(steps), "success": success_count})
            if success_count >= len(steps) * 0.7:
                speak("Task completed Sir."); return True
            else:
                speak(f"Task partially done Sir. {success_count} of {len(steps)} steps succeeded.")
                return False
        except Exception as e:
            print(f"[AGENT] Error: {e}")
            speak(f"Task failed Sir. Error: {str(e)[:80]}")
            return False
        finally:
            self.is_executing = False

_agent = DesktopAgent()

def run_agent(goal):   return _agent.execute_task(goal)
def needs_agent(text): return is_complex_task(text)