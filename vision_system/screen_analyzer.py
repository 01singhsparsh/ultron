import os, sys, re
import psutil
from PIL import ImageGrab
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def get_active_window():
    try:
        import pygetwindow as gw
        win = gw.getActiveWindow()
        if win: return {"title":win.title,"width":win.width,"height":win.height,"x":win.left,"y":win.top}
    except: pass
    return {}

def get_running_processes():
    processes = []
    try:
        for proc in psutil.process_iter(['name','pid','memory_percent']):
            try:
                if proc.info['memory_percent'] > 0.1:
                    processes.append({"name":proc.info['name'],"pid":proc.info['pid'],"memory":round(proc.info['memory_percent'],1)})
            except: pass
        processes.sort(key=lambda x: x['memory'], reverse=True)
        return processes[:10]
    except: return []

def get_system_state():
    try:
        cpu  = psutil.cpu_percent(interval=1)
        ram  = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        batt = psutil.sensors_battery()
        return {"cpu":cpu,"ram":ram.percent,"disk":disk.percent,
                "battery":int(batt.percent) if batt else None,"plugged":batt.power_plugged if batt else None}
    except: return {}

def analyze_screen(detailed=False):
    from vision_system.ocr_engine import get_screen_text
    screen_text  = get_screen_text()
    active_win   = get_active_window()
    system_state = get_system_state()
    processes    = get_running_processes()
    analysis     = {"screen_text":screen_text[:2000],"active_window":active_win,
                    "system_state":system_state,"top_processes":processes[:5]}
    if GROQ_API_KEY and (detailed or len(screen_text) > 100):
        analysis["description"] = _describe_screen(screen_text, active_win, processes)
    return analysis

def _describe_screen(text, window, processes):
    if not GROQ_API_KEY: return ""
    try:
        from groq import Groq
        win_title  = window.get("title","unknown")
        proc_names = ", ".join([p["name"] for p in processes[:5]])
        prompt     = (f"Active window: {win_title}\nRunning apps: {proc_names}\n"
                     f"Screen text:\n{text[:1500]}\n\nDescribe what Sparsh Sir is currently doing. Max 2 sentences.")
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"system","content":"You are ULTRON analyzing a computer screen. Be specific and concise."},
                      {"role":"user","content":prompt}],
            max_tokens=150, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e: return f"Screen description error: {e}"

def what_is_on_screen():
    analysis = analyze_screen(detailed=True)
    return analysis.get("description", f"Active window: {analysis.get('active_window',{}).get('title','unknown')}")

def read_screen_text():
    from vision_system.ocr_engine import get_screen_text
    text = get_screen_text()
    return text if text else "Sir, I could not detect any readable text on screen."

def get_screen_summary():
    analysis    = analyze_screen(detailed=True)
    state       = analysis.get("system_state",{})
    win         = analysis.get("active_window",{})
    description = analysis.get("description","")
    summary     = ""
    if win.get("title"):    summary += f"Active: {win['title']}. "
    if description:         summary += description
    if state:               summary += f" CPU: {state.get('cpu',0)}%, RAM: {state.get('ram',0)}%."
    return summary or "Sir, could not analyze the screen."
