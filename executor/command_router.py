"""
command_router.py
The brain of the execution layer.
Classifies every command and routes to the correct executor.
LLM is NEVER used for actions — only for answers.
"""
import re, os, sys, json
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIAS_FILE = os.path.join(BASE_DIR, "executor", "alias_database.json")

def _load_aliases() -> dict:
    try:
        with open(ALIAS_FILE) as f:
            return json.load(f)
    except: return {}

def _load_key() -> str:
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    return line.split("=")[1].strip().strip('"').strip("'")
    except: pass
    return ""

# ── Classification patterns ──
OPEN_PATTERNS = [
    r'^open\s+(.+)',
    r'^launch\s+(.+)',
    r'^start\s+(.+)',
    r'^run\s+(.+)',
    r'^go to\s+(.+)',
    r'^show me\s+(.+)',
    r'^load\s+(.+)',
]

CLOSE_PATTERNS = [
    r'^close\s+(.+)',
    r'^quit\s+(.+)',
    r'^exit\s+(.+)',
    r'^kill\s+(.+)',
    r'^shut down\s+(.+)',
]

WINDOW_PATTERNS = [
    r'^minimize\s+(.+)',
    r'^maximise\s+(.+)',
    r'^maximize\s+(.+)',
    r'^restore\s+(.+)',
    r'^switch to\s+(.+)',
    r'^focus on\s+(.+)',
    r'^bring up\s+(.+)',
    r'^go back to\s+(.+)',
]

SCREEN_PATTERNS = [
    r"what('?s| is) (on |open on )?(my )?screen",
    r"what (apps?|windows?) (are |is )?(open|running)",
    r"what (am i|are you) (looking at|seeing)",
    r"what('?s| is) open",
    r"what('?s| is) running",
    r"describe (my )?screen",
    r"what do you see",
]

WHATSAPP_PATTERNS = [
    r'send\s+(.+?)\s+(a\s+)?(?:whatsapp\s+)?message\s+(.+)',
    r'message\s+(.+?)\s+(?:saying|that|on whatsapp)?\s+(.+)',
    r'whatsapp\s+(.+?)\s+(?:saying|that)?\s+(.+)',
    r'text\s+(.+?)\s+(.+)',
]

WEBSITE_KEYWORDS = set()

def _get_website_keywords() -> set:
    global WEBSITE_KEYWORDS
    if WEBSITE_KEYWORDS: return WEBSITE_KEYWORDS
    aliases = _load_aliases().get("websites", {})
    WEBSITE_KEYWORDS = set(aliases.keys())
    return WEBSITE_KEYWORDS

def _is_website(name: str) -> bool:
    """Check if name refers to a website."""
    name_lower = name.lower().strip()
    websites   = _get_website_keywords()
    if name_lower in websites: return True
    if "." in name_lower and " " not in name_lower: return True
    # Common website words
    web_words = ["website","site","page","web","url",".com",".in",".org",".io"]
    return any(w in name_lower for w in web_words)

def _is_app(name: str) -> bool:
    """Check if name refers to a desktop app."""
    aliases   = _load_aliases().get("apps", {})
    name_lower= name.lower().strip()
    if name_lower in aliases: return True
    for key in aliases:
        if key in name_lower or name_lower in key:
            return True
    return False

def classify_and_execute(text: str) -> dict:
    """
    Main router — classify command and execute it.
    Returns: {handled, success, response, action_type}
    """
    t = text.lower().strip()
    # Remove wake words
    for w in ["ultron","hey ultron","hello ultron"]:
        t = t.replace(w,"").strip()

    # ── SCREEN CONTEXT ──
    for pattern in SCREEN_PATTERNS:
        if re.search(pattern, t):
            from executor.screen_context import describe_screen
            desc = describe_screen()
            return {
                "handled":     True,
                "success":     True,
                "response":    f"Sir, {desc}",
                "action_type": "screen_context"
            }

    # ── WINDOW ACTIONS ──
    for pattern in WINDOW_PATTERNS:
        match = re.match(pattern, t)
        if match:
            app_name = match.group(1).strip()
            action   = pattern.split(r'\s')[0].replace('^','')
            from executor.window_manager import execute_window_action
            result = execute_window_action(action, app_name)
            return {
                "handled":     True,
                "success":     result["success"],
                "response":    result["message"],
                "action_type": "window_action"
            }

    # ── CLOSE APP ──
    for pattern in CLOSE_PATTERNS:
        match = re.match(pattern, t)
        if match:
            app_name = match.group(1).strip()
            from executor.app_launcher import close_app
            result = close_app(app_name)
            return {
                "handled":     True,
                "success":     result["success"],
                "response":    result["message"],
                "action_type": "close_app"
            }

    # ── OPEN COMMAND ──
    for pattern in OPEN_PATTERNS:
        match = re.match(pattern, t)
        if match:
            target = match.group(1).strip()

            # Website or app?
            if _is_website(target) and not _is_app(target):
                from executor.website_launcher import open_website
                result = open_website(target)
                return {
                    "handled":     True,
                    "success":     result["success"],
                    "response":    result["message"],
                    "action_type": "open_website"
                }
            elif _is_app(target):
                from executor.app_launcher import launch_app
                result = launch_app(target)
                return {
                    "handled":     True,
                    "success":     result["success"],
                    "response":    result["message"],
                    "action_type": "open_app"
                }
            else:
                # Unknown — try app first then website
                from executor.app_launcher   import launch_app
                from executor.website_launcher import open_website
                app_result = launch_app(target)
                if app_result["success"]:
                    return {
                        "handled":     True,
                        "success":     True,
                        "response":    app_result["message"],
                        "action_type": "open_app"
                    }
                web_result = open_website(target)
                return {
                    "handled":     True,
                    "success":     web_result["success"],
                    "response":    web_result["message"],
                    "action_type": "open_website"
                }

    # ── WHATSAPP SEND ──
    for pattern in WHATSAPP_PATTERNS:
        match = re.match(pattern, t)
        if match:
            groups  = match.groups()
            contact = groups[0].strip() if groups else ""
            message = groups[-1].strip() if len(groups) > 1 else ""
            if contact and message:
                from modules.speaker  import speak
                from modules.listener import listen
                speak(f"Sir, I will send '{message}' to {contact}. Shall I send?")
                confirm = listen(timeout=5, phrase_limit=5)
                if confirm and any(w in confirm.lower() for w in ["yes","sure","send","okay","haan"]):
                    from executor.whatsapp_controller import send_message
                    result = send_message(contact, message)
                    return {
                        "handled":     True,
                        "success":     result["success"],
                        "response":    result["message"],
                        "action_type": "whatsapp_send"
                    }
                else:
                    return {
                        "handled":     True,
                        "success":     True,
                        "response":    "Message not sent Sir.",
                        "action_type": "whatsapp_cancelled"
                    }

    # ── SHOW DESKTOP ──
    if any(p in t for p in ["show desktop","go to desktop","minimize all","minimise all"]):
        from executor.window_manager import show_desktop
        result = show_desktop()
        return {
            "handled":     True,
            "success":     result["success"],
            "response":    "Desktop shown Sir.",
            "action_type": "show_desktop"
        }

    # Not handled by executor — let LLM answer
    return {"handled": False}