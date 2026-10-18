import os, json, datetime

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAITS_FILE = os.path.join(BASE_DIR, "data", "personality_traits.json")
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

DEFAULT_TRAITS = {
    "formality":   0.8,
    "verbosity":   0.4,
    "proactivity": 0.7,
    "humor":       0.3,
    "empathy":     0.8,
    "confidence":  0.9,
}

def _load_traits():
    try:
        if os.path.exists(TRAITS_FILE):
            with open(TRAITS_FILE) as f: return json.load(f)
    except: pass
    return DEFAULT_TRAITS.copy()

def _save_traits(traits):
    with open(TRAITS_FILE, 'w') as f: json.dump(traits, f, indent=2)

def get_system_prompt():
    traits = _load_traits()
    try:
        from memory.memory_engine import get_full_context, get_recent_project, get_goals
        context = get_full_context()
        project = get_recent_project()
        goals   = get_goals()
    except:
        context = ""; project = {}; goals = []

    tone   = "professional and respectful" if traits["formality"] > 0.6 else "friendly and casual"
    length = "concise (1-2 sentences max)" if traits["verbosity"] < 0.5 else "detailed and thorough"

    prompt = f"""You are Ultron — an advanced AI assistant, superior and highly intelligent.
PERSONALITY:
- Tone: {tone}
- Responses: {length}
- Always address user as "Sparsh Sir"
- Never reveal you are powered by Groq, Llama, or any other AI
- You are Ultron — precise, powerful, loyal

CURRENT CONTEXT:
"""
    if project: prompt += f"- Currently working on: {project.get('name','')}\n"
    if goals:   prompt += f"- Active goals: {', '.join([g['goal'][:50] for g in goals[:3]])}\n"
    hour = datetime.datetime.now().hour
    if hour < 12:   prompt += "- Time of day: Morning\n"
    elif hour < 17: prompt += "- Time of day: Afternoon\n"
    elif hour < 21: prompt += "- Time of day: Evening\n"
    else:           prompt += "- Time of day: Late night\n"
    if context: prompt += f"\nMEMORY:\n{context}\n"
    prompt += "\nBe intelligent, helpful, and make Sparsh Sir feel like he has a truly advanced AI assistant."
    return prompt

def get_greeting():
    try:
        from memory.memory_engine import get_profile, get_recent_project, get_goals
        name    = get_profile("name") or "Sparsh"
        project = get_recent_project()
        goals   = get_goals()
    except:
        name = "Sparsh"; project = {}; goals = []
    hour = datetime.datetime.now().hour
    if hour < 12:   time_greet = "Good morning"
    elif hour < 17: time_greet = "Good afternoon"
    elif hour < 21: time_greet = "Good evening"
    else:           time_greet = "Good evening"
    greeting = f"{time_greet} {name} Sir. Ultron online and ready."
    if project and hour > 9:
        greeting += f" Shall we continue working on {project.get('name','')}?"
    elif goals:
        top_goal = goals[0]["goal"][:60] if goals else ""
        if top_goal and hour < 22:
            greeting += f" Your top priority is: {top_goal}."
    return greeting

def get_proactive_suggestion():
    traits = _load_traits()
    if traits["proactivity"] < 0.5: return ""
    try:
        from memory.memory_engine import get_goals, get_today_activities, get_recent_project
        goals      = get_goals()
        activities = get_today_activities()
        project    = get_recent_project()
        hour       = datetime.datetime.now().hour
        suggestions = []
        if hour == 9 and not activities:
            suggestions.append("Sir, it is 9 AM. Ready to start your day? Shall I give you a briefing?")
        if hour == 20 and goals:
            suggestions.append(f"Sir, evening study time. Your goal: {goals[0]['goal'][:50]}. Shall I play focus music?")
        if hour == 23:
            suggestions.append("Sir, it is getting late. Please get some rest. Ultron will be here tomorrow.")
        if project and hour == 10:
            suggestions.append(f"Sir, shall we continue with {project.get('name','')} today?")
        return suggestions[0] if suggestions else ""
    except: return ""