import os, json, datetime

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONV_FILE = os.path.join(BASE_DIR, "data", "conversations.json")
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

def save_exchange(user_text, ultron_reply, mood="neutral"):
    convs = _load_conversations()
    convs.append({
        "timestamp": str(datetime.datetime.now()),
        "date":      str(datetime.date.today()),
        "user":      user_text,
        "ultron":    ultron_reply,
        "mood":      mood,
    })
    convs = convs[-200:]
    with open(CONV_FILE, 'w', encoding='utf-8') as f: json.dump(convs, f, indent=2)
    try:
        from memory.semantic_memory import store_conversation
        store_conversation(user_text, ultron_reply)
    except: pass

def _load_conversations():
    try:
        if os.path.exists(CONV_FILE):
            with open(CONV_FILE, encoding='utf-8') as f: return json.load(f)
    except: pass
    return []

def get_recent(n=5): return _load_conversations()[-n:]

def get_today():
    today = str(datetime.date.today())
    return [c for c in _load_conversations() if c.get("date") == today]

def get_context_string(n=3):
    recent = get_recent(n)
    if not recent: return ""
    context = "RECENT CONVERSATION:\n"
    for c in recent:
        context += f"User: {c['user']}\nULTRON: {c.get('ultron','')}\n"
    return context

def summarize_today():
    today_convs = get_today()
    if not today_convs: return "No conversations today yet."
    topics = []
    for c in today_convs:
        u = c.get("user","").lower()
        if "python"           in u: topics.append("Python")
        if "machine learning" in u: topics.append("ML")
        if "ultron"           in u: topics.append("ULTRON project")
        if "study"            in u: topics.append("Studying")
    summary = f"Today: {len(today_convs)} conversations. "
    if topics: summary += f"Topics: {', '.join(list(set(topics))[:5])}."
    return summary