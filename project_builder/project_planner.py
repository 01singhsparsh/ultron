"""
project_planner.py
Plans complete project structure before any code is written.
Decides files, architecture, dependencies, and build order.
"""
import os, sys, json
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

def plan_project(description: str) -> dict:
    """
    Takes a project description and returns a complete project plan.
    Returns dict with: name, type, files, dependencies, run_command
    """
    if not GROQ_API_KEY:
        return {}

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        system = """You are ULTRON's Project Planner â€” an expert software architect.
Plan a complete project based on the description.

Return ONLY valid JSON in this exact format:
{
  "name": "project_name_snake_case",
  "title": "Human Readable Title",
  "type": "python_gui|python_cli|web|python_script",
  "description": "what this project does",
  "files": [
    {
      "filename": "main.py",
      "description": "Main entry point",
      "is_main": true
    },
    {
      "filename": "utils.py",
      "description": "Utility functions",
      "is_main": false
    }
  ],
  "dependencies": ["tkinter", "json", "os"],
  "run_command": "python main.py",
  "features": ["feature1", "feature2", "feature3"]
}

RULES:
- For GUI apps use tkinter (built-in, no install needed)
- For web apps create index.html + style.css + script.js
- Keep it simple but fully functional
- Maximum 5 files
- Only use standard library or commonly installed packages
"""

        response = client.chat.completions.create(
            model       = "qwen/qwen3.8-27b",
            messages    = [
                {"role": "system", "content": system},
                {"role": "user",   "content": f"Plan this project: {description}"}
            ],
            max_tokens  = 800,
            temperature = 0.2
        )

        raw = response.choices[0].message.content.strip()
        if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```"   in raw: raw = raw.split("```")[1].split("```")[0].strip()

        start = raw.find("{"); end = raw.rfind("}") + 1
        if start != -1 and end > start:
            plan = json.loads(raw[start:end])
            print(f"[PLANNER] Project plan created: {plan.get('title','?')}")
            print(f"[PLANNER] Files: {[f['filename'] for f in plan.get('files',[])]}")
            print(f"[PLANNER] Type: {plan.get('type','?')}")
            return plan

    except Exception as e:
        print(f"[PLANNER] Error: {e}")

    # Fallback plan
    return {
        "name":         "my_project",
        "title":        "My Project",
        "type":         "python_script",
        "description":  description,
        "files":        [{"filename":"main.py","description":"Main script","is_main":True}],
        "dependencies": [],
        "run_command":  "python main.py",
        "features":     []
    }

def get_project_folder(project_name: str) -> str:
    """Get the folder where the project will be saved."""
    desktop  = os.path.join(os.path.expanduser("~"), "Desktop")
    projects = os.path.join(desktop, "ULTRON_Projects")
    folder   = os.path.join(projects, project_name)
    os.makedirs(folder, exist_ok=True)
    return folder

