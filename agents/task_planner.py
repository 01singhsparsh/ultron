import json, os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

AVAILABLE_ACTIONS = """
AVAILABLE ACTIONS:
- open_app(app_name), close_app(app_name), focus_app(app_name)
- type_text(text), press_key(key), mouse_click(x,y), mouse_move(x,y)
- open_url(url), search_web(query), download_file(url,path)
- run_command(cmd), create_file(path,content), read_file(path)
- delete_file(path), create_folder(path), list_files(path)
- copy_file(src,dst), move_file(src,dst)
- install_software(name), take_screenshot(), scroll(direction,amount)
- wait(seconds), speak(text)
"""

def plan_task(goal, context=""):
    if not GROQ_API_KEY:
        return [{"action":"speak","params":{"text":"No API key configured Sir."}}]
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        system_prompt = f"""You are ULTRON's task planning engine.
Break down the goal into specific executable steps.
{AVAILABLE_ACTIONS}
RULES:
1. Return ONLY a valid JSON array. Nothing else.
2. Each step must have: "action", "params", "description"
3. Be specific with exact names, URLs, commands
4. Add wait steps between actions needing time
5. Add speak steps to inform user of progress
6. Maximum 15 steps
Context: {context}"""
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {"role":"system","content":system_prompt},
                {"role":"user","content":f"Create step-by-step plan for: {goal}"}
            ],
            max_tokens=1000, temperature=0.2)
        raw = response.choices[0].message.content.strip()
        if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```"   in raw: raw = raw.split("```")[1].split("```")[0].strip()
        start = raw.find("["); end = raw.rfind("]") + 1
        if start != -1 and end > start: raw = raw[start:end]
        steps = json.loads(raw)
        print(f"[PLANNER] Generated {len(steps)} steps for: {goal}")
        return steps
    except json.JSONDecodeError as e:
        print(f"[PLANNER] JSON error: {e}")
        return [{"action":"speak","params":{"text":"I had trouble planning that task Sir."}}]
    except Exception as e:
        print(f"[PLANNER] Error: {e}")
        return [{"action":"speak","params":{"text":f"Planning error Sir: {str(e)[:100]}"}}]

def is_complex_task(user_text):
    complex_keywords = [
        "install","download","set up","setup","create a project",
        "build","automate","find and","search and","open and",
        "go to","navigate","fill","submit","book","order",
        "write a","make a","generate","research and summarize",
        "do my","complete my","help me with my project"
    ]
    t = user_text.lower()
    return any(kw in t for kw in complex_keywords)

