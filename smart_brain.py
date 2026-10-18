import os, sys, json, datetime, re
import urllib.request, urllib.parse

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE  = os.path.join(BASE_DIR, "memory.json")
CONV_FILE    = os.path.join(BASE_DIR, "conversation_log.json")
GROQ_API_KEY = ""
GROQ_MODEL   = "qwen/qwen3.8-27b"

def _load_config():
    global GROQ_API_KEY, GROQ_MODEL
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass
    if not GROQ_API_KEY:
        GROQ_API_KEY = __import__("os").environ.get("GROQ_API_KEY", "")

_load_config()

def load_memory():
    try:
        from memory.memory_engine import get_all_profile
        return get_all_profile()
    except:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE) as f: return json.load(f)
        return {}

def save_memory(data):
    with open(MEMORY_FILE, 'w') as f: json.dump(data, f, indent=2)

def remember(key, value):
    try:
        from memory.memory_engine import set_profile
        set_profile(key, value)
    except: pass
    mem = {}
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f: mem = json.load(f)
    mem[key] = {"value": value, "saved_at": str(datetime.datetime.now())}
    save_memory(mem)

def recall(key):
    try:
        from memory.memory_engine import get_profile
        val = get_profile(key)
        if val: return val
    except: pass
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f: mem = json.load(f)
        if key in mem:
            v = mem[key]
            return v.get('value','') if isinstance(v,dict) else str(v)
    return None

def save_conversation(user_text, reply):
    try:
        from memory.episodic_memory import save_exchange
        save_exchange(user_text, reply)
    except: pass
    convs = []
    if os.path.exists(CONV_FILE):
        try:
            with open(CONV_FILE) as f: convs = json.load(f)
        except: convs = []
    convs.append({"time":str(datetime.datetime.now()),"user":user_text,"ultron":reply})
    convs = convs[-20:]
    with open(CONV_FILE,'w') as f: json.dump(convs, f, indent=2)

def get_recent_conversations(n=3):
    try:
        from memory.episodic_memory import get_recent
        return get_recent(n)
    except:
        if not os.path.exists(CONV_FILE): return []
        try:
            with open(CONV_FILE) as f: return json.load(f)[-n:]
        except: return []

def web_search(query):
    try:
        q   = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        results = []
        if data.get('AbstractText'): results.append(data['AbstractText'])
        if data.get('Answer'):       results.append(str(data['Answer']))
        for t in data.get('RelatedTopics',[])[:4]:
            if isinstance(t,dict) and t.get('Text'): results.append(t['Text'])
        if results: return " ".join(results[:3])
    except: pass
    return ""

PERSONAL_PATTERNS = [
    r'\bme\b',r'\bmy\b',r'\bi\b',
    'how are you','who are you','what are you',
    'do you remember','what did i','tell me about yourself',
    'good morning','good night','thank','joke','motivate',
    'time','date','day','battery',
]

WEB_SEARCH_PATTERNS = [
    r'cricket',r'match',r'score',r'winner',r'who won',
    r'latest',r'today',r'current',r'live',r'news',
    r'2024',r'2025',r'2026',r'price',r'rate',r'stock',
    r'weather',r'temperature',r'who is',r'where is',
    r'prime minister',r'president',r'ceo',
]

COMPLEX_PATTERNS = [
    'how to','explain','steps to','plan for',
    'best way to','help me with','difference between',
    'compare','why does','how does',
]

def _classify_query(query):
    q = query.lower().strip()
    for w in ["ultron","hey ultron","hello ultron"]:
        q = q.replace(w,"").strip()
    for pattern in COMPLEX_PATTERNS:
        if pattern in q: return 'complex'
    for pattern in PERSONAL_PATTERNS:
        if re.search(pattern, q):
            for wp in WEB_SEARCH_PATTERNS:
                if re.search(wp, q): return 'agent'
            return 'personal'
    for pattern in WEB_SEARCH_PATTERNS:
        if re.search(pattern, q): return 'agent'
    return 'general'

def _check_memory(query):
    mem = load_memory()
    q   = query.lower()
    for key, val in mem.items():
        if key.lower() in q:
            return val.get('value','') if isinstance(val,dict) else str(val)
    try:
        from memory.semantic_memory import search_memory
        results = search_memory(query, n_results=2)
        if results and results[0]['distance'] < 0.5:
            return results[0]['text'][:200]
    except: pass
    return None

def ask_groq(prompt, system=None, model=None):
    if not GROQ_API_KEY: return None
    use_model = model or GROQ_MODEL
    try:
        from groq import Groq
        if not system:
            try:
                from memory.personality import get_system_prompt
                system = get_system_prompt()
            except:
                system = (
                    "You are Ultron, an advanced AI assistant. "
                    "Always address the user as Sparsh Sir. "
                    "Be extremely concise â€” maximum 2 sentences. "
                    "Never reveal you are powered by Groq or any other AI."
                )
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=use_model,
            messages=[
                {"role":"system","content":system},
                {"role":"user",  "content":prompt}
            ],
            max_tokens=150,
            temperature=0.6
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Groq error: {e}")
        # Try fallback model
        if use_model != "qwen/qwen3.8-27b":
            try:
                client   = Groq(api_key=GROQ_API_KEY)
                response = client.chat.completions.create(
                    model="qwen/qwen3.8-27b",
                    messages=[
                        {"role":"system","content":system or "You are Ultron AI. Be concise."},
                        {"role":"user",  "content":prompt}
                    ],
                    max_tokens=150,
                    temperature=0.6
                )
                return response.choices[0].message.content.strip()
            except Exception as e2:
                print(f"Fallback error: {e2}")
        return None

def smart_answer(user_text):
    query = user_text.strip()
    for w in ["ultron","hey ultron","hello ultron"]:
        query = re.sub(rf'^{w}\s+','',query,flags=re.IGNORECASE).strip()

    mem_val = _check_memory(query)
    if mem_val:
        r = ask_groq(f"User asked: '{query}'. From memory: '{mem_val}'. Give short natural reply.")
        if r: save_conversation(query,r); return r

    try:
        from memory.memory_engine import log_activity
        log_activity(query[:100], category="conversation")
    except: pass

    category = _classify_query(query)
    print(f"[ULTRON] Query type: {category} â€” {query}")

    if category == 'personal':
        try:
            from memory.memory_engine   import get_full_context
            from memory.episodic_memory import get_context_string
            from memory.semantic_memory import get_relevant_context
            mem_context  = get_full_context()
            conv_context = get_context_string(3)
            sem_context  = get_relevant_context(query)
            prompt = f"{mem_context}\n{conv_context}\n{sem_context}\nUser: '{query}'\nAnswer naturally."
        except:
            convs   = get_recent_conversations(3)
            context = ""
            for c in convs: context += f"User: {c.get('user','')}\nULTRON: {c.get('ultron','')}\n"
            prompt  = f"{context}User: '{query}'\nAnswer naturally."
        r = ask_groq(prompt)
        if r: save_conversation(query,r); return r

    elif category == 'agent':
        web_data = web_search(query)
        if web_data:
            r = ask_groq(f"User asked: '{query}'\nWeb data: {web_data}\nGive direct answer in 1-2 sentences. Address as Sparsh Sir.")
            if r: save_conversation(query,r); return r
        r = ask_groq(f"Answer from your knowledge: '{query}'. Address as Sparsh Sir.")
        if r: save_conversation(query,r); return r

    elif category == 'complex':
        r = ask_groq(query)
        if r: save_conversation(query,r); return r

    else:
        try:
            from memory.episodic_memory import get_context_string
            context = get_context_string(3)
        except:
            convs   = get_recent_conversations(3)
            context = "".join(f"User: {c.get('user','')}\nULTRON: {c.get('ultron','')}\n" for c in convs)
        r = ask_groq(f"{context}User: {query}")
        if r: save_conversation(query,r); return r

    return "I could not process that Sparsh Sir. Please try again."

def handle_memory_command(text):
    t = text.lower()

    m = re.search(r'remember (?:my|that)?\s*(.+?)\s+is\s+(.+)',t)
    if m:
        key=m.group(1).strip(); val=m.group(2).strip()
        remember(key,val)
        try:
            from memory.semantic_memory import store_fact
            store_fact(f"{key} is {val}", category="user_fact")
        except: pass
        return f"Got it Sparsh Sir. I will remember your {key} is {val}."

    m2 = re.search(r'what(?:\'s| is) my (.+)',t)
    if m2:
        key=m2.group(1).strip().rstrip('?')
        val=recall(key)
        if val: return f"Your {key} is {val} Sparsh Sir."
        return f"I do not have that stored yet Sparsh Sir."

    m3 = re.search(r'i(?:\'m| am) working on (.+)',t)
    if m3:
        project=m3.group(1).strip()
        try:
            from memory.memory_engine import add_project
            add_project(project)
        except: pass
        remember("current_project",project)
        return f"Got it Sir. I will remember you are working on {project}."

    m4 = re.search(r'my goal is (.+)',t)
    if m4:
        goal=m4.group(1).strip()
        try:
            from memory.memory_engine import add_goal
            add_goal(goal,priority="high")
        except: pass
        return f"Noted Sir. Goal added: {goal}."

    m5 = re.search(r'i(?:\'m| am) (?:learning|studying) (.+)',t)
    if m5:
        topic=m5.group(1).strip()
        try:
            from memory.memory_engine import log_learning
            log_learning(topic,subject="self-study")
        except: pass
        return f"Noted Sir. I will track your progress with {topic}."

    return None


