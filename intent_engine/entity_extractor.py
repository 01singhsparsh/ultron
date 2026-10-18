"""
entity_extractor.py
Extracts entities from natural language.
Handles English, Hindi, Hinglish.
"""
import re, json, os
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIAS_FILE = os.path.join(BASE_DIR, "executor", "alias_database.json")

def _load_aliases() -> dict:
    try:
        with open(ALIAS_FILE) as f: return json.load(f)
    except: return {}

# ── Known entity lists ──
KNOWN_APPS = [
    "brave","chrome","firefox","edge","vs code","vscode","code",
    "spotify","discord","whatsapp","telegram","notepad","calculator",
    "explorer","terminal","cmd","powershell","task manager","settings",
    "word","excel","powerpoint","zoom","obs","steam","vlc",
]

KNOWN_WEBSITES = [
    "chatgpt","youtube","github","linkedin","instagram","gmail",
    "google","twitter","reddit","netflix","amazon","flipkart",
    "google drive","google maps","notion","figma","canva",
    "claude","gemini","perplexity","colab","hugging face",
    "whatsapp web","stackoverflow","discord",
]

WINDOW_ACTIONS = {
    "minimize":  ["minimize","minimise","chota","chhota","hata","hatao","band karo window"],
    "maximize":  ["maximize","maximise","bada","fullscreen","full screen","bada karo"],
    "close":     ["close","band","bandh","quit","exit","hatao"],
    "focus":     ["switch to","focus","go to","bring up","le ao"],
    "restore":   ["restore","wapas lao","normal karo"],
}

TIME_PATTERNS = {
    "yesterday":  ["yesterday","kal","kal raat","last night","pehle din"],
    "today":      ["today","aaj","abhi"],
    "last_week":  ["last week","pichle hafte","week ago"],
    "morning":    ["morning","subah","savere"],
    "evening":    ["evening","shaam","raat"],
}

def extract_entities(text: str, intent: str) -> dict:
    """
    Extract all relevant entities from text based on intent.
    Returns dict of extracted entities.
    """
    t       = text.lower().strip()
    aliases = _load_aliases()
    entities= {}

    # ── App entity ──
    for app in KNOWN_APPS:
        if app in t:
            entities["app"] = app
            break
    if not entities.get("app"):
        for key in aliases.get("apps", {}):
            if key in t:
                entities["app"] = key
                break

    # ── Website entity ──
    for site in KNOWN_WEBSITES:
        if site in t:
            entities["website"] = site
            break
    if not entities.get("website"):
        for key in aliases.get("websites", {}):
            if key in t:
                entities["website"] = key
                break

    # ── Contact/Recipient entity ──
    if intent == "SEND_MESSAGE":
        entities["recipient"] = _extract_recipient(text)
        entities["message"]   = _extract_message_content(text)
        entities["platform"]  = _extract_platform(text)

    # ── Window action ──
    if intent == "WINDOW_ACTION":
        for action, keywords in WINDOW_ACTIONS.items():
            if any(kw in t for kw in keywords):
                entities["window_action"] = action
                break
        # Find target window
        for app in KNOWN_APPS:
            if app in t:
                entities["window_target"] = app
                break

    # ── Time entity ──
    for time_key, keywords in TIME_PATTERNS.items():
        if any(kw in t for kw in keywords):
            entities["time_ref"] = time_key
            break

    # ── Search query ──
    if intent == "SEARCH_WEB":
        query = _extract_search_query(text)
        if query: entities["query"] = query

    # ── Project name ──
    project = _extract_project(text)
    if project: entities["project"] = project

    # ── File/folder ──
    file_match = re.search(r'(?:file|folder|directory)\s+(?:called|named)?\s*["\']?([^"\']+)["\']?', t)
    if file_match: entities["file"] = file_match.group(1).strip()

    return entities

def _extract_recipient(text: str) -> str:
    """Extract message recipient from text."""
    t = text.lower()
    # Hindi patterns: "Rahul ko", "Sparsh ko message", "mom ko"
    hindi_match = re.search(r'([a-z]+)\s+ko\b', t)
    if hindi_match:
        name = hindi_match.group(1)
        if name not in ["message","whatsapp","koi","kuch","bhej"]:
            return name.title()

    # English patterns: "send Rahul", "message to Rahul", "text Rahul"
    eng_patterns = [
        r'send\s+(?:a\s+)?message\s+to\s+([a-z]+)',
        r'message\s+([a-z]+)',
        r'text\s+([a-z]+)',
        r'whatsapp\s+([a-z]+)',
        r'tell\s+([a-z]+)',
        r'send\s+([a-z]+)',
    ]
    for pat in eng_patterns:
        m = re.search(pat, t)
        if m:
            name = m.group(1)
            if name not in ["me","him","her","them","us","a","the","on"]:
                return name.title()
    return ""

def _extract_message_content(text: str) -> str:
    """Extract the actual message content."""
    t = text.lower()
    # After "saying", "that", "ki", "bolo"
    patterns = [
        r'saying\s+["\']?(.+?)["\']?$',
        r'\bthat\b\s+(.+?)$',
        r'\bki\b\s+(.+?)$',
        r'\bbolo\b\s+(.+?)$',
        r'\bbolna\b\s+(.+?)$',
        r'"([^"]+)"',
        r"'([^']+)'",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            content = m.group(1).strip()
            if len(content) > 1:
                return content
    return ""

def _extract_platform(text: str) -> str:
    t = text.lower()
    if "whatsapp" in t: return "whatsapp"
    if "telegram" in t: return "telegram"
    if "email"    in t or "mail" in t: return "email"
    return "whatsapp"  # default

def _extract_search_query(text: str) -> str:
    t = text
    patterns = [
        r'search\s+(?:for\s+)?(.+)',
        r'google\s+(.+)',
        r'find\s+(.+)\s+online',
        r'look up\s+(.+)',
    ]
    for pat in patterns:
        m = re.search(pat, t, re.IGNORECASE)
        if m: return m.group(1).strip()
    return ""

def _extract_project(text: str) -> str:
    t = text.lower()
    # Known project keywords
    projects = ["ultron","jarvis","ml project","machine learning","ai project",
                "gaming mode","portfolio","website project","college project"]
    for proj in projects:
        if proj in t: return proj
    # "my X project" pattern
    m = re.search(r'my\s+([a-z\s]+)\s+project', t)
    if m: return m.group(1).strip()
    return ""