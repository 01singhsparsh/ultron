import os, subprocess, webbrowser, datetime, platform, random, threading, time, glob
from modules.speaker import speak
from modules.logger  import log

def _open(app_name, fallback_path=None):
    try:
        if fallback_path and os.path.exists(fallback_path):
            subprocess.Popen([fallback_path]); return True
        subprocess.Popen(["start","",app_name], shell=True); return True
    except: return False

def _open_browser(url): webbrowser.open(url)

def _launch_whatsapp():
    """Launch WhatsApp — works for both regular and Beta."""
    import psutil
    # Check if already running
    for proc in psutil.process_iter(['name']):
        try:
            if 'whatsapp' in proc.info['name'].lower():
                try:
                    import pygetwindow as gw
                    for win in gw.getAllWindows():
                        if 'whatsapp' in win.title.lower():
                            win.activate(); return True
                except: pass
                return True
        except: pass
    # Launch via protocol
    try:
        subprocess.Popen(
            ['powershell','-Command','start-process whatsapp:'],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        time.sleep(5)
        return True
    except: pass
    webbrowser.open("https://web.whatsapp.com")
    return False

def _focus_whatsapp():
    """Bring WhatsApp window to front."""
    try:
        import pygetwindow as gw
        for win in gw.getAllWindows():
            if 'whatsapp' in win.title.lower():
                win.restore(); win.activate()
                time.sleep(0.5); return True
    except: pass
    return False

def open_chrome(cmd):
    speak("Opening Chrome Sir.")
    _open("chrome")

def open_brave(cmd):
    speak("Opening Brave Sir.")
    paths = [
        "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
        "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
        os.path.join(os.environ.get("LOCALAPPDATA",""),
                     "BraveSoftware\\Brave-Browser\\Application\\brave.exe"),
    ]
    for p in paths:
        if os.path.exists(p): subprocess.Popen([p]); return
    subprocess.Popen("start brave", shell=True)

def open_youtube(cmd):
    speak("Opening YouTube Sir.")
    webbrowser.open("https://www.youtube.com")

def open_vscode(cmd):
    speak("Opening VS Code Sir.")
    _open("code")

def open_notepad(cmd):
    speak("Opening Notepad Sir.")
    subprocess.Popen(["notepad.exe"])

def open_spotify(cmd):
    speak("Opening Spotify Sir.")
    _open("spotify")

def open_whatsapp(cmd):
    speak("Opening WhatsApp Sir.")
    _launch_whatsapp()

def open_calculator(cmd):
    speak("Opening Calculator Sir.")
    subprocess.Popen("calc.exe", shell=True)

def open_settings(cmd):
    speak("Opening Settings Sir.")
    subprocess.Popen("start ms-settings:", shell=True)

def open_explorer(cmd):
    speak("Opening File Explorer Sir.")
    subprocess.Popen("explorer.exe")

def open_taskman(cmd):
    speak("Opening Task Manager Sir.")
    subprocess.Popen("taskmgr.exe")

def open_camera(cmd):
    speak("Opening Camera Sir.")
    subprocess.Popen("start microsoft.windows.camera:", shell=True)

def open_maps(cmd):
    speak("Opening Maps Sir.")
    webbrowser.open("https://maps.google.com")

def open_gmail(cmd):
    speak("Opening Gmail Sir.")
    webbrowser.open("https://mail.google.com")

def open_instagram(cmd):
    speak("Opening Instagram Sir.")
    webbrowser.open("https://www.instagram.com")

def open_twitter(cmd):
    speak("Opening Twitter Sir.")
    webbrowser.open("https://www.twitter.com")

def search_google(cmd):
    query = cmd.lower()
    for p in ["search google for","search for","google","search"]:
        query = query.replace(p,"").strip()
    if query:
        speak(f"Searching {query} Sir.")
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ','+')}")
    else:
        speak("What to search Sir?")

def search_youtube(cmd):
    query = cmd.lower()
    for p in ["search youtube for","play on youtube","play song","play music",
              "play","youtube search","youtube","search for","search"]:
        query = query.replace(p,"").strip()
    if not query:
        speak("What should I play Sir?"); return
    speak(f"Playing {query} Sir.")
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
        except: pass
    threading.Thread(target=_auto_click, daemon=True).start()

def tell_time(cmd):
    speak(f"Sir, time is {datetime.datetime.now().strftime('%I:%M %p')}.")

def tell_date(cmd):
    speak(f"Today is {datetime.date.today().strftime('%A, %d %B %Y')} Sir.")

def tell_day(cmd):
    speak(f"Today is {datetime.datetime.now().strftime('%A')} Sir.")

def set_alarm(cmd):
    import re
    text  = cmd.lower()
    match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text)
    if match:
        hour   = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3)
        if period == 'pm' and hour != 12: hour += 12
        elif period == 'am' and hour == 12: hour = 0
        now        = datetime.datetime.now()
        alarm_time = now.replace(hour=hour,minute=minute,second=0,microsecond=0)
        if alarm_time < now: alarm_time += datetime.timedelta(days=1)
        diff    = (alarm_time-now).total_seconds()
        display = alarm_time.strftime('%I:%M %p')
        speak(f"Alarm set for {display} Sir.")
        def _ring():
            time.sleep(diff)
            for _ in range(3):
                speak(f"Sir! Wake up! It is {display}!")
                time.sleep(2)
        threading.Thread(target=_ring, daemon=True).start()
    else:
        speak("Please say the time clearly Sir. For example, set alarm for 7 AM.")

def cancel_alarm(cmd):
    speak("All alarms cancelled Sir.")

def daily_briefing(cmd):
    now  = datetime.datetime.now()
    hour = now.hour
    if hour < 12:   greeting = "Good morning"
    elif hour < 17: greeting = "Good afternoon"
    else:           greeting = "Good evening"
    speak(f"{greeting} Sir! Here is your daily briefing.")
    time.sleep(0.3)
    speak(f"Today is {now.strftime('%A, %d %B %Y')}.")
    time.sleep(0.3)
    speak(f"Current time is {now.strftime('%I:%M %p')}.")
    time.sleep(0.3)
    try:
        import psutil
        b = psutil.sensors_battery()
        if b: speak(f"Battery is at {int(b.percent)} percent.")
    except: pass
    speak("Have a productive day Sir!")

NOTES_FILE = os.path.join(os.path.expanduser("~"),"Desktop","ultron_notes.txt")

def take_note(cmd):
    import re
    note = re.sub(r'(take a note|take note|note down|make a note|note)\s*','',
                  cmd,flags=re.IGNORECASE).strip()
    if not note:
        speak("What should I note down Sir?")
        from modules.listener import listen
        note = listen(timeout=8,phrase_limit=15)
        if not note: speak("Did not catch that Sir."); return
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %I:%M %p")
    with open(NOTES_FILE,'a',encoding='utf-8') as f:
        f.write(f"[{timestamp}] {note}\n")
    speak("Noted Sir.")

def read_notes(cmd):
    if not os.path.exists(NOTES_FILE): speak("No notes found Sir."); return
    with open(NOTES_FILE,'r',encoding='utf-8') as f: lines = f.readlines()
    if not lines: speak("Your notes are empty Sir."); return
    speak(f"You have {len(lines)} notes Sir. Here are the last 3.")
    for line in lines[-3:]: speak(line.strip()); time.sleep(0.3)

def clear_notes(cmd):
    if os.path.exists(NOTES_FILE): open(NOTES_FILE,'w').close()
    speak("All notes cleared Sir.")

def open_notes(cmd):
    speak("Opening your notes Sir.")
    if not os.path.exists(NOTES_FILE): open(NOTES_FILE,'w').close()
    subprocess.Popen(["notepad",NOTES_FILE])

def find_downloads(cmd):
    speak("Opening Downloads Sir.")
    subprocess.Popen(f'explorer "{os.path.join(os.path.expanduser("~"),"Downloads")}"',shell=True)

def find_desktop(cmd):
    speak("Opening Desktop Sir.")
    subprocess.Popen(f'explorer "{os.path.join(os.path.expanduser("~"),"Desktop")}"',shell=True)

def find_documents(cmd):
    speak("Opening Documents Sir.")
    subprocess.Popen(f'explorer "{os.path.join(os.path.expanduser("~"),"Documents")}"',shell=True)

def find_pictures(cmd):
    speak("Opening Pictures Sir.")
    subprocess.Popen(f'explorer "{os.path.join(os.path.expanduser("~"),"Pictures")}"',shell=True)

def set_reminder(cmd):
    import re
    match = re.search(r'(\d+)\s*minute',cmd.lower())
    if match:
        mins = int(match.group(1))
        text = re.sub(r'remind me (in \d+ minutes? ?(to)?|to)','',cmd.lower()).strip() or "your reminder"
        speak(f"Reminder set for {mins} minutes Sir.")
        def _r():
            time.sleep(mins*60)
            speak(f"Sir, reminder: {text}")
        threading.Thread(target=_r,daemon=True).start()
    else:
        speak("Please say remind me in 5 minutes to drink water Sir.")

def check_battery(cmd):
    try:
        import psutil
        b = psutil.sensors_battery()
        if b: speak(f"Battery is {int(b.percent)} percent, {'plugged in' if b.power_plugged else 'on battery'} Sir.")
        else: speak("Could not read battery Sir.")
    except: speak("Please install psutil Sir.")

def volume_up(cmd):
    speak("Increasing volume Sir.")
    try: subprocess.call("nircmd.exe changesysvolume 2000",shell=True)
    except: pass

def volume_down(cmd):
    speak("Decreasing volume Sir.")
    try: subprocess.call("nircmd.exe changesysvolume -2000",shell=True)
    except: pass

def volume_mute(cmd):
    speak("Muting Sir.")
    try: subprocess.call("nircmd.exe mutesysvolume 1",shell=True)
    except: pass

def volume_unmute(cmd):
    speak("Unmuting Sir.")
    try: subprocess.call("nircmd.exe mutesysvolume 0",shell=True)
    except: pass

def shutdown_pc(cmd):
    speak("Shutting down in 10 seconds Sir.")
    subprocess.call("shutdown /s /t 10",shell=True)

def restart_pc(cmd):
    speak("Restarting in 10 seconds Sir.")
    subprocess.call("shutdown /r /t 10",shell=True)

def sleep_pc(cmd):
    speak("Sleeping now Sir.")
    subprocess.call("rundll32.exe powrprof.dll,SetSuspendState 0,1,0",shell=True)

def cancel_shutdown(cmd):
    speak("Cancelled Sir.")
    subprocess.call("shutdown /a",shell=True)

def lock_pc(cmd):
    speak("Locking Sir.")
    subprocess.call("rundll32.exe user32.dll,LockWorkStation",shell=True)

def take_screenshot(cmd):
    try:
        import pyautogui
        f = os.path.join(os.path.expanduser("~"),"Desktop",
                        f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        pyautogui.screenshot(f)
        speak("Screenshot saved to Desktop Sir.")
    except: speak("Could not take screenshot Sir.")

def get_weather(cmd): speak("Opening weather Sir."); webbrowser.open("https://www.weather.com")
def get_news(cmd):    speak("Opening news Sir.");    webbrowser.open("https://news.google.com")
def cricket_score(cmd): speak("Opening cricket scores Sir."); webbrowser.open("https://www.cricbuzz.com")

def who_are_you(cmd):
    speak(random.choice([
        "I am Ultron, your advanced AI assistant Sir.",
        "Ultron — designed to be better than human Sir."
    ]))

def how_are_you(cmd):
    speak(random.choice([
        "All systems operational Sir.",
        "Functioning at peak efficiency Sir."
    ]))

def tell_joke(cmd):
    speak(random.choice([
        "Why do programmers prefer dark mode? Light attracts bugs Sir.",
        "Why was the computer cold? It left its Windows open Sir.",
        "I would tell you a joke about UDP but you might not get it Sir."
    ]))

def motivate_me(cmd):
    speak(random.choice([
        "Believe you can and you are halfway there Sir.",
        "Every expert was once a beginner Sir. Keep pushing.",
        "The harder you work, the luckier you get Sir."
    ]))

def say_thanks(cmd):
    speak(random.choice(["Always a pleasure Sir.","Happy to help Sir.","Anytime Sir."]))

def good_morning(cmd): speak("Good morning Sir! Ready to assist you today.")
def good_night(cmd):   speak("Good night Sir. Rest well.")
def flip_coin(cmd):    speak(f"It is {random.choice(['Heads','Tails'])} Sir.")
def roll_dice(cmd):    speak(f"You got {random.randint(1,6)} Sir.")

def roast_me(cmd):
    speak(random.choice([
        "Sir, I would roast you but I am not allowed to burn trash.",
        "Sir, you are not stupid. You just have bad luck thinking.",
    ]))

def mood_music(cmd):
    c = cmd.lower()
    if any(w in c for w in ["happy","party","dance"]):
        speak("Playing happy music Sir!")
        webbrowser.open("https://www.youtube.com/results?search_query=happy+party+songs+playlist")
    elif any(w in c for w in ["sad","cry","emotional"]):
        speak("Playing soothing music Sir.")
        webbrowser.open("https://www.youtube.com/results?search_query=sad+emotional+songs+playlist")
    elif any(w in c for w in ["focus","study","concentrate"]):
        speak("Playing focus music Sir.")
        webbrowser.open("https://www.youtube.com/results?search_query=study+focus+music+lofi")
    elif any(w in c for w in ["sleep","relax"]):
        speak("Playing relaxing music Sir.")
        webbrowser.open("https://www.youtube.com/results?search_query=relaxing+sleep+music")
    elif any(w in c for w in ["workout","gym","exercise"]):
        speak("Playing workout music Sir!")
        webbrowser.open("https://www.youtube.com/results?search_query=gym+workout+motivation+songs")
    else:
        speak("Playing good music Sir!")
        webbrowser.open("https://www.youtube.com/results?search_query=best+hindi+songs+playlist+2024")

def calculate(cmd):
    import re
    text = cmd.lower()
    text = text.replace("what is","").replace("calculate","").replace("ultron","")
    text = text.replace("plus","+").replace("minus","-").replace("times","*")
    text = text.replace("multiplied by","*").replace("divided by","/")
    perc = re.search(r'(\d+\.?\d*)\s*percent\s*of\s*(\d+\.?\d*)',text)
    if perc:
        speak(f"Sir, the answer is {float(perc.group(1))*float(perc.group(2))/100}."); return
    expr = re.sub(r'[^0-9+\-*/().\s]','',text).strip()
    if expr:
        try: speak(f"Sir, the answer is {eval(expr)}.")
        except: speak("Sorry Sir, could not calculate that.")
    else:
        speak("Please say a calculation Sir.")

def translate(cmd):
    import re
    match = re.search(r'translate\s+(.+?)\s+(?:in|to|into)\s+(\w+)',cmd.lower())
    if match:
        speak(f"Translating {match.group(1)} to {match.group(2)} Sir.")
        webbrowser.open(
            f"https://translate.google.com/?sl=auto&tl={match.group(2)}"
            f"&text={match.group(1).replace(' ','+')}&op=translate"
        )
    else:
        speak("Please say translate hello in French Sir.")

def type_text(cmd):
    import re, pyautogui
    text = re.sub(r'(type|write|type this|write this)\s*','',cmd,flags=re.IGNORECASE).strip()
    if not text:
        speak("What should I type Sir?")
        from modules.listener import listen
        text = listen(timeout=8,phrase_limit=15)
        if not text: speak("Did not catch that Sir."); return
    speak("Typing Sir.")
    time.sleep(1)
    pyautogui.typewrite(text,interval=0.05)

def close_app(cmd):
    import re
    app = re.sub(r'(close|kill|exit|shut)\s*','',cmd.lower(),flags=re.IGNORECASE).strip()
    app_map = {
        "chrome":"chrome.exe","brave":"brave.exe","notepad":"notepad.exe",
        "spotify":"Spotify.exe","whatsapp":"WhatsApp.exe",
        "calculator":"calculator.exe","vs code":"code.exe","vscode":"code.exe",
        "task manager":"taskmgr.exe","word":"WINWORD.EXE","excel":"EXCEL.EXE",
        "edge":"msedge.exe","firefox":"firefox.exe",
    }
    for key,exe in app_map.items():
        if key in app:
            speak(f"Closing {key} Sir.")
            subprocess.call(f"taskkill /f /im {exe}",shell=True)
            return
    speak(f"Closing {app} Sir.")
    subprocess.call(f"taskkill /f /im {app}.exe",shell=True)

def system_status(cmd):
    try:
        import psutil
        cpu  = psutil.cpu_percent(interval=1)
        ram  = psutil.virtual_memory()
        batt = psutil.sensors_battery()
        speak("System status Sir.")
        time.sleep(0.3); speak(f"CPU is {cpu} percent.")
        time.sleep(0.3); speak(f"RAM is {ram.percent} percent used.")
        if batt: time.sleep(0.3); speak(f"Battery is {int(batt.percent)} percent.")
    except: speak("Please install psutil Sir.")

def brightness_up(cmd):
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness(min(100,sbc.get_brightness()[0]+20))
        speak("Brightness increased Sir.")
    except: speak("Increasing brightness Sir.")

def brightness_down(cmd):
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness(max(10,sbc.get_brightness()[0]-20))
        speak("Brightness decreased Sir.")
    except: speak("Decreasing brightness Sir.")

def live_weather(cmd):
    import re, urllib.request
    city_match = re.search(r'(?:weather in|temperature in|weather)\s+([a-zA-Z\s]+)',cmd.lower())
    city = city_match.group(1).strip() if city_match else "Delhi"
    try:
        url = f"https://wttr.in/{city.replace(' ','+')}?format=3"
        req = urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=5) as r:
            speak(f"Sir, {r.read().decode().strip()}")
    except:
        speak(f"Opening weather for {city} Sir.")
        webbrowser.open(f"https://www.google.com/search?q=weather+in+{city.replace(' ','+')}")

def read_news_headlines(cmd):
    import urllib.request, re
    try:
        speak("Fetching top news Sir.")
        url = "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"
        req = urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=6) as r:
            content = r.read().decode('utf-8')
        titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>',content)
        if not titles: titles = re.findall(r'<title>(.*?)</title>',content)
        headlines = [t for t in titles[1:6] if t and 'Times of India' not in t]
        if headlines:
            speak(f"Here are the top {len(headlines)} headlines Sir.")
            for i,h in enumerate(headlines,1):
                speak(f"Headline {i}: {h}"); time.sleep(0.5)
        else:
            speak("Could not fetch headlines Sir."); webbrowser.open("https://news.google.com")
    except:
        speak("Opening Google News Sir."); webbrowser.open("https://news.google.com")

def open_file(cmd):
    import re
    name = re.sub(r'(open|find|show|my)\s*','',cmd,flags=re.IGNORECASE).strip()
    if not name: speak("Which file Sir?"); return
    found = []
    for d in ["Desktop","Documents","Downloads"]:
        found.extend(glob.glob(os.path.join(os.path.expanduser("~"),d,f"*{name}*")))
    if found:
        speak(f"Opening {os.path.basename(found[0])} Sir.")
        os.startfile(found[0])
    else:
        speak(f"Could not find {name} Sir.")

def make_ppt(cmd):
    import re
    topic = re.sub(
        r'(make|create|build|generate|prepare|ppt|powerpoint|presentation|slides?)\s*(?:on|about|for)?\s*',
        '',cmd,flags=re.IGNORECASE).strip()
    if not topic:
        speak("What topic Sir?")
        from modules.listener import listen
        topic = listen(timeout=8,phrase_limit=10)
        if not topic: return
    speak(f"Opening Gamma for presentation on {topic} Sir.")
    webbrowser.open(
        f"https://gamma.app/create/generate?prompt=Create+a+professional+presentation+on+{topic.replace(' ','+')}"
    )

def make_document(cmd):
    speak("Opening Google Docs Sir.")
    webbrowser.open("https://docs.google.com/document/create")

# ── WhatsApp Functions ──
def whatsapp_open_chat(cmd):
    """Open specific contact WhatsApp chat."""
    import re
    patterns = [
        r'open (?:chat|chats) of (.+)',
        r'open (.+?)(?:\'s)? (?:chat|whatsapp)',
        r'whatsapp (.+)',
    ]
    contact = None
    for pattern in patterns:
        m = re.search(pattern,cmd.lower())
        if m:
            contact = m.group(1).strip()
            for f in ["please","sir","the","a"]:
                contact = contact.replace(f,"").strip()
            break

    if not contact:
        speak("Who should I open the chat for Sir?")
        from modules.listener import listen
        contact = listen(timeout=5)
        if not contact: return

    speak(f"Opening {contact.title()}'s chat Sir.")
    _launch_whatsapp()

    try:
        import pyautogui
        _focus_whatsapp()
        time.sleep(0.5)
        pyautogui.hotkey('ctrl','f')
        time.sleep(0.8)
        pyautogui.hotkey('ctrl','a')
        pyautogui.typewrite(contact,interval=0.05)
        time.sleep(1.5)
        pyautogui.press('enter')
        time.sleep(0.5)
        speak(f"Opened {contact.title()}'s chat Sir.")
    except Exception as e:
        print(f"[WA] Chat error: {e}")
        speak("Could not open chat Sir.")

def whatsapp_send_message(cmd):
    """Send message in currently open WhatsApp chat."""
    import re, pyautogui
    patterns = [
        r'send (?:her|him|them|message)?\s*(?:that|saying|:)?\s*(.+)',
        r'message (?:that|saying|:)?\s*(.+)',
        r'type (.+)',r'write (.+)',
    ]
    message = None
    for pattern in patterns:
        m = re.search(pattern,cmd.lower())
        if m: message = m.group(1).strip(); break

    if not message:
        speak("What message should I send Sir?")
        from modules.listener import listen
        message = listen(timeout=8,phrase_limit=15)
        if not message: return

    speak("Sending message Sir.")
    try:
        _focus_whatsapp()
        time.sleep(0.5)
        screen_w,screen_h = pyautogui.size()
        pyautogui.click(screen_w//2,int(screen_h*0.93))
        time.sleep(0.4)
        pyautogui.typewrite(message,interval=0.04)
        time.sleep(0.3)
        pyautogui.press('enter')
        speak("Message sent Sir.")
    except Exception as e:
        print(f"[WA] Send error: {e}")
        speak("Could not send Sir. WhatsApp may not be open.")

def whatsapp_full_flow(cmd):
    """
    Complete flow — open contact chat AND send message.
    Say: send Tanisha kal se mai nhi aaunga
    Say: message Rahul hello bhai
    """
    import re, pyautogui
    patterns = [
        r'send\s+(.+?)\s+(?:that\s+|saying\s+|message\s+|ki\s+|ko?\s+)(.+)',
        r'message\s+(.+?)\s+(?:that\s+|saying\s+|ki\s+|ko?\s+)(.+)',
        r'(?:send|bhej)\s+(.+?)\s+ko\s+(?:ki\s+|ke?\s+)?(.+)',
        r'whatsapp\s+(.+?)\s+(?:that\s+|saying\s+|ki\s+)?(.+)',
        r'(.+?)\s+ko\s+(?:message\s+)?(?:bhej|send|bol)\s+(?:ki\s+|ke?\s+)?(.+)',
        r'send\s+(.+?)\s+(.+)',
    ]
    contact = None; message = None
    for pattern in patterns:
        m = re.search(pattern,cmd.lower())
        if m:
            contact = m.group(1).strip()
            message = m.group(2).strip()
            for f in ["please","sir","the","a","bhai","yaar"]:
                contact = contact.replace(f,"").strip()
            if contact and message and len(contact) > 1:
                break

    if not contact or not message:
        whatsapp_send_message(cmd); return

    speak(f"Sending message to {contact.title()} Sir.")
    _launch_whatsapp()

    try:
        _focus_whatsapp()
        time.sleep(0.5)
        # Search contact
        pyautogui.hotkey('ctrl','f')
        time.sleep(0.8)
        pyautogui.hotkey('ctrl','a')
        pyautogui.typewrite(contact,interval=0.05)
        time.sleep(1.5)
        pyautogui.press('enter')
        time.sleep(1.0)
        # Type and send
        screen_w,screen_h = pyautogui.size()
        pyautogui.click(screen_w//2,int(screen_h*0.93))
        time.sleep(0.4)
        pyautogui.typewrite(message,interval=0.04)
        time.sleep(0.3)
        pyautogui.press('enter')
        speak(f"Message sent to {contact.title()} Sir.")
    except Exception as e:
        print(f"[WA] Full flow error: {e}")
        speak("Could not send Sir. Please try manually.")

def whatsapp_message(cmd): whatsapp_full_flow(cmd)
def whatsapp_reply(cmd):   whatsapp_send_message(cmd)

def read_my_screen(cmd):
    speak("Scanning your screen Sir.")
    try:
        from vision import read_screen
        speak(read_screen())
    except: speak("Vision module not available Sir.")

def fix_screen_error(cmd):
    speak("Analyzing screen for errors Sir.")
    def _fix():
        try:
            from vision_system.vision_agent import fix_screen_error as fse
            result = fse()
            speak(result[:300] if len(result)>300 else result)
        except: speak("Vision system not available Sir.")
    threading.Thread(target=_fix,daemon=True).start()

def describe_my_screen(cmd):
    speak("Analyzing your screen Sir.")
    def _desc():
        try:
            from vision_system.screen_analyzer import what_is_on_screen
            speak(what_is_on_screen())
        except: speak("Vision system not available Sir.")
    threading.Thread(target=_desc,daemon=True).start()

def ingest_knowledge(cmd):
    speak("Ingesting documents Sir.")
    def _ingest():
        try:
            from second_brain.ingestion import ingest_folder,get_knowledge_dir
            count = ingest_folder(get_knowledge_dir())
            speak(f"Done Sir. Ingested {count} documents." if count>0
                  else "Sir, add your files to the knowledge folder first.")
        except Exception as e:
            speak(f"Ingestion error Sir: {e}")
    threading.Thread(target=_ingest,daemon=True).start()

def ask_knowledge(cmd):
    import re
    question = re.sub(
        r'(ask knowledge|search knowledge|from knowledge|from my notes?|from my pdf)\s*',
        '',cmd,flags=re.IGNORECASE).strip()
    if not question:
        speak("What do you want to know Sir?")
        from modules.listener import listen
        question = listen(timeout=8,phrase_limit=15)
        if not question: return
    speak("Searching your knowledge base Sir.")
    def _ask():
        try:
            from second_brain.rag_engine import answer_from_knowledge
            result = answer_from_knowledge(question)
            speak(result["answer"])
        except: speak("Knowledge base not available Sir.")
    threading.Thread(target=_ask,daemon=True).start()

def open_pipeline(cmd):
    speak("Opening Pipeline Mode Sir.")
    try:
        from pipeline.pipeline_mode import start_pipeline
        start_pipeline()
    except Exception as e:
        speak(f"Could not start Pipeline Mode Sir.")

def start_gaming_mode(cmd):
    speak("Switching to Gaming Mode Sir. Launching Asphalt 9.")
    def _go():
        try:
            from gaming_mode.gaming_mode import start_gaming_mode as sgm
            sgm("asphalt")
        except Exception as e:
            speak(f"Gaming mode error Sir: {e}")
    threading.Thread(target=_go,daemon=True).start()

def stop_gaming_mode(cmd):
    speak("Exiting Gaming Mode Sir.")
    try:
        from gaming_mode.gaming_mode import stop_gaming_mode as stgm
        stgm()
    except: pass

def organize_my_downloads(cmd):
    speak("Organizing your Downloads folder Sir.")
    try:
        from agents.file_agent import organize_downloads
        result = organize_downloads()
        if result: speak(f"Done Sir. Organized {len(result)} files.")
        else: speak("Downloads folder is already organized Sir.")
    except: speak("Could not organize downloads Sir.")

def build_project(cmd):
    import re
    task = re.sub(
        r'^(ultron\s+|hey\s+ultron\s+|build me|build|create|make|develop|code me)\s*',
        '',cmd,flags=re.IGNORECASE).strip()
    if not task:
        speak("What would you like me to build Sir?")
        from modules.listener import listen
        task = listen(timeout=8,phrase_limit=15)
        if not task: return
    speak("Starting autonomous build Sir.")
    def _build():
        try:
            from project_builder.builder import build_project as bp
            bp(task)
        except Exception as e:
            speak(f"Build error Sir: {e}")
    threading.Thread(target=_build,daemon=True).start()

def system_state(cmd):
    try:
        import psutil
        cpu  = psutil.cpu_percent(interval=1)
        ram  = psutil.virtual_memory().percent
        batt = psutil.sensors_battery()
        msg  = f"CPU {int(cpu)} percent. RAM {int(ram)} percent."
        if batt: msg += f" Battery {int(batt.percent)} percent."
        speak(msg)
    except: speak("Could not get system state Sir.")

def open_earth_mode(cmd):
    from earth_mode.earth_mode import start_earth_mode
    import threading
    threading.Thread(target=start_earth_mode, daemon=True).start()

def earth_navigate(cmd):
    from earth_mode.earth_mode import handle_earth_command
    handle_earth_command(cmd)

COMMAND_MAP = {
    # Apps
    "open chrome":open_chrome,"open google chrome":open_chrome,
    "open brave":open_brave,"launch brave":open_brave,"brave":open_brave,
    "open youtube":open_youtube,
    "open vs code":open_vscode,"open visual studio":open_vscode,
    "open notepad":open_notepad,
    "open spotify":open_spotify,
    "open whatsapp":open_whatsapp,
    "open calculator":open_calculator,
    "open settings":open_settings,
    "open file explorer":open_explorer,"open files":open_explorer,
    "open task manager":open_taskman,
    "open camera":open_camera,
    "open maps":open_maps,
    "open gmail":open_gmail,
    "open instagram":open_instagram,
    "open twitter":open_twitter,
    # Search/Play
    "search google":search_google,"search for":search_google,
    "google search":search_google,"google":search_google,
    "search youtube":search_youtube,"play on youtube":search_youtube,
    "play song":search_youtube,"play music":search_youtube,
    "youtube":search_youtube,
    # Time
    "what time":tell_time,"tell me the time":tell_time,
    "current time":tell_time,"what is the time":tell_time,
    "what date":tell_date,"today's date":tell_date,"today date":tell_date,
    "what day":tell_day,"which day":tell_day,
    # Alarm/Reminder
    "set alarm":set_alarm,"alarm for":set_alarm,"wake me up":set_alarm,
    "cancel alarm":cancel_alarm,"stop alarm":cancel_alarm,
    "remind me":set_reminder,"set reminder":set_reminder,
    # Notes
    "daily briefing":daily_briefing,"briefing":daily_briefing,
    "take a note":take_note,"take note":take_note,
    "note down":take_note,"make a note":take_note,"note":take_note,
    "read my notes":read_notes,"read notes":read_notes,"my notes":read_notes,
    "clear notes":clear_notes,"delete notes":clear_notes,
    "open notes":open_notes,"show notes":open_notes,
    # Folders
    "open downloads":find_downloads,"open desktop":find_desktop,
    "open documents":find_documents,"open pictures":find_pictures,
    # Battery/System
    "battery":check_battery,"battery status":check_battery,
    "system status":system_status,"cpu":system_status,
    "system state":system_state,"what is running":system_state,
    # Volume
    "volume up":volume_up,"increase volume":volume_up,"louder":volume_up,
    "volume down":volume_down,"decrease volume":volume_down,"quieter":volume_down,
    "mute":volume_mute,"unmute":volume_unmute,
    # Power
    "shutdown":shutdown_pc,"shut down":shutdown_pc,
    "restart":restart_pc,"reboot":restart_pc,
    "sleep pc":sleep_pc,"hibernate":sleep_pc,
    "cancel shutdown":cancel_shutdown,
    "lock":lock_pc,"lock screen":lock_pc,
    # Screenshot
    "take screenshot":take_screenshot,"screenshot":take_screenshot,
    # Brightness
    "brightness up":brightness_up,"increase brightness":brightness_up,
    "brightness down":brightness_down,"decrease brightness":brightness_down,
    # Weather/News
    "weather in":live_weather,"live weather":live_weather,
    "temperature in":live_weather,"weather":get_weather,
    "news":get_news,
    "read news":read_news_headlines,"read headlines":read_news_headlines,
    "top news":read_news_headlines,"headlines":read_news_headlines,
    "cricket":cricket_score,"cricket score":cricket_score,
    # Fun
    "who are you":who_are_you,"what are you":who_are_you,
    "how are you":how_are_you,
    "tell me a joke":tell_joke,"joke":tell_joke,
    "motivate me":motivate_me,"inspire me":motivate_me,
    "thank you":say_thanks,"thanks":say_thanks,
    "good morning":good_morning,"good night":good_night,
    "flip a coin":flip_coin,"flip coin":flip_coin,
    "roll a dice":roll_dice,"roll dice":roll_dice,
    "roast me":roast_me,
    "play something happy":mood_music,"play something sad":mood_music,
    "play focus music":mood_music,"play workout music":mood_music,
    "play sleep music":mood_music,"mood music":mood_music,
    # Utility
    "calculate":calculate,"how much is":calculate,
    "translate":translate,
    "type":type_text,"write":type_text,
    "close":close_app,"kill":close_app,
    "open my":open_file,"find my":open_file,
    "make a ppt":make_ppt,"make ppt":make_ppt,"create ppt":make_ppt,
    "create presentation":make_ppt,"ppt on":make_ppt,
    "make a document":make_document,"create document":make_document,
    # WhatsApp
    "open chat of":whatsapp_open_chat,
    "open chats of":whatsapp_open_chat,
    "open whatsapp chat":whatsapp_open_chat,
    "send message to":whatsapp_full_flow,
    "send":whatsapp_full_flow,
    "message to":whatsapp_full_flow,
    "whatsapp message":whatsapp_full_flow,
    "reply":whatsapp_reply,
    # Vision
    "what is on my screen":read_my_screen,
    "read my screen":read_my_screen,
    "describe my screen":describe_my_screen,
    "fix error on screen":fix_screen_error,
    "fix the error":fix_screen_error,
    # Knowledge
    "ingest knowledge":ingest_knowledge,"ingest documents":ingest_knowledge,
    "ask knowledge":ask_knowledge,"search knowledge":ask_knowledge,
    "from my notes":ask_knowledge,"from my pdf":ask_knowledge,
    # Earth Mode
    "open earth mode":open_earth_mode,
    "earth mode":open_earth_mode,
    "maps mode":open_earth_mode,
    "open maps mode":open_earth_mode,
    "holographic earth":open_earth_mode,
    "show earth":open_earth_mode,
    "show me":earth_navigate,
    "take me to":earth_navigate,
    "satellite mode":earth_navigate,
    "earth at night":earth_navigate,
    "reset view":earth_navigate,
    "exit earth mode":earth_navigate,    
# Pipeline/Gaming
    "open pipeline":open_pipeline,"pipeline mode":open_pipeline,
    "gaming mode":start_gaming_mode,"game mode":start_gaming_mode,
    "switch to gaming mode":start_gaming_mode,
    "stop gaming mode":stop_gaming_mode,"exit gaming mode":stop_gaming_mode,
    # Files/Build
    "organize my downloads":organize_my_downloads,
    "organize downloads":organize_my_downloads,
    "build me a":build_project,"build a":build_project,
    "create an app":build_project,"make an app":build_project,
}

def handle_command(user_text):
    text_lower = user_text.lower().strip()
    best_key, best_len = None, 0
    for key in COMMAND_MAP:
        if key in text_lower and len(key) > best_len:
            best_key, best_len = key, len(key)
    if best_key:
        log(f"Command matched: '{best_key}'")
        try: COMMAND_MAP[best_key](user_text)
        except Exception as e:
            log(f"Command error: {e}",level="ERROR")
            speak("Something went wrong Sir.")
        return True
    return False