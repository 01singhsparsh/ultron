import os, sys, re
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from multi_agent.base_agent import BaseAgent

class VisionAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="VISION", role="Screen understanding error detection and UI analysis", max_tokens=300)

    def run(self, task, context=None):
        self.log(f"Vision task: {task}")
        task_lower = task.lower()
        if any(w in task_lower for w in ['error','bug','fix','crash','exception','traceback']):
            from vision_system.error_detector import analyze_screen_for_errors
            result = analyze_screen_for_errors()
            if result.get("has_error"):
                return {"agent":"vision_agent","task":task,
                        "answer":f"{result.get('explanation','')} Fix: {result.get('fix','')}","success":True}
            return {"agent":"vision_agent","task":task,"answer":result.get("message","No errors detected Sir."),"success":True}
        elif any(w in task_lower for w in ['read','text','what does it say','ocr']):
            from vision_system.screen_analyzer import read_screen_text
            text = read_screen_text()
            return {"agent":"vision_agent","task":task,"answer":text[:500],"success":bool(text)}
        elif any(w in task_lower for w in ['describe','what is','what am i','what are you looking']):
            from vision_system.screen_analyzer import what_is_on_screen
            desc = what_is_on_screen()
            return {"agent":"vision_agent","task":task,"answer":desc,"success":bool(desc)}
        else:
            from vision_system.screen_analyzer import analyze_screen
            analysis = analyze_screen(detailed=True)
            return {"agent":"vision_agent","task":task,"answer":analysis.get("description",""),"success":True}

_vision_agent = None

def get_vision_agent():
    global _vision_agent
    if _vision_agent is None: _vision_agent = VisionAgent()
    return _vision_agent

def analyze_screen_now():    return get_vision_agent().run("describe screen").get("answer","")
def fix_screen_error():
    result = get_vision_agent().run("fix error on screen")
    return result.get("answer","No errors detected Sir.")
def read_screen_now():       return get_vision_agent().run("read screen text").get("answer","")