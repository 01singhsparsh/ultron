"""
classifier.py
Intent classifier — understands WHAT user wants regardless of HOW they say it.
Supports English, Hindi, Hinglish naturally.
"""
import re, os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Intent definitions with multilingual patterns ──
INTENTS = {
    "OPEN_APP": {
        "patterns": [
            r'\bopen\b',r'\blaunch\b',r'\bstart\b',r'\brun\b',
            r'\bkhol\b',r'\bchalu\b',r'\bshuru\b',r'\bkaro\b',
            r'\bload\b',r'\bfire up\b',
        ],
        "anti_patterns": [r'\bclose\b',r'\bband\b',r'\bshutdown\b']
    },
    "CLOSE_APP": {
        "patterns": [
            r'\bclose\b',r'\bquit\b',r'\bexit\b',r'\bkill\b',
            r'\bband\b',r'\bbandh\b',r'\bshutdown\b',r'\bterminate\b'
        ],
        "anti_patterns": []
    },
    "SEND_MESSAGE": {
        "patterns": [
            r'\bsend\b',r'\bmessage\b',r'\btext\b',r'\bwhatsapp\b',
            r'\bbhej\b',r'\bbhejo\b',r'\bbol\b',r'\bbolna\b',
            r'\bbata\b',r'\bbatao\b',r'\btype\b',r'\bkaro\b.*\bmessage\b',
            r'\bko message\b',r'\bko whatsapp\b',r'\bko bhej\b',
        ],
        "anti_patterns": []
    },
    "OPEN_WEBSITE": {
        "patterns": [
            r'\bopen\b.*\b(com|in|org|io|net)\b',
            r'\bgo to\b',r'\bnavigate\b',r'\bbrowse\b',
            r'\bchatgpt\b',r'\byoutube\b',r'\bgithub\b',r'\bgmail\b',
            r'\binstagram\b',r'\blinkedin\b',r'\bchrome\b.*\bopen\b',
            r'\bwebsite\b',r'\bsite\b',
        ],
        "anti_patterns": []
    },
    "WINDOW_ACTION": {
        "patterns": [
            r'\bminimize\b',r'\bmaximize\b',r'\brestore\b',
            r'\bswitch to\b',r'\bfocus on\b',r'\bbring up\b',
            r'\bchota\b',r'\bbada\b',r'\bhata\b',r'\bband karo\b',
        ],
        "anti_patterns": []
    },
    "SCREEN_CONTEXT": {
        "patterns": [
            r'what.*open',r'what.*screen',r'what.*running',
            r'what.*see',r'describe.*screen',r'kya.*khula',
            r'kya.*chal raha',r'screen pe kya',
        ],
        "anti_patterns": []
    },
    "CONTINUE_WORK": {
        "patterns": [
            r'\bcontinue\b',r'\bresume\b',r'\brestore\b.*\bwork\b',
            r'\bwhere.*left\b',r'\blast session\b',r'\byesterday.*work\b',
            r'\bwahi se\b',r'\bwapas\b',r'\bfir se\b.*\bkaam\b',
            r'\bcontinue.*project\b',r'\bopen.*last\b',
        ],
        "anti_patterns": []
    },
    "SEARCH_WEB": {
        "patterns": [
            r'\bsearch\b',r'\bgoogle\b',r'\bfind\b.*\bonline\b',
            r'\blook up\b',r'\bdhundo\b',r'\bsearch karo\b',
            r'\bkya hai\b',r'\bwhat is\b',r'\bwho is\b',
        ],
        "anti_patterns": [r'\bopen\b']
    },
    "TAKE_NOTE": {
        "patterns": [
            r'\bnote\b',r'\bremember\b',r'\bwrite down\b',
            r'\blikho\b',r'\byaad rakh\b',r'\bnote karo\b',
        ],
        "anti_patterns": []
    },
    "SET_ALARM": {
        "patterns": [
            r'\balarm\b',r'\bwake me\b',r'\bremind me\b',
            r'\btimer\b',r'\bjagao\b',r'\balarm laga\b',
        ],
        "anti_patterns": []
    },
    "SYSTEM_INFO": {
        "patterns": [
            r'\bbattery\b',r'\bcpu\b',r'\bram\b',r'\bsystem\b.*\bstatus\b',
            r'\bkitni battery\b',r'\bram kitna\b',r'\bsystem kaisa\b',
        ],
        "anti_patterns": []
    },
    "PLAY_MEDIA": {
        "patterns": [
            r'\bplay\b',r'\bmusic\b',r'\bsong\b',r'\bvideo\b',
            r'\bchala\b',r'\bgana\b',r'\bsuno\b',r'\byoutube\b.*\bplay\b',
        ],
        "anti_patterns": []
    },
    "GAMING_MODE": {
        "patterns": [
            r'\bgaming mode\b',r'\bgame mode\b',r'\bplay.*game\b',
            r'\basphalt\b',r'\bgaming\b.*\bstart\b',
        ],
        "anti_patterns": []
    },
    "GENERAL_QA": {
        "patterns": [
            r'\bwhat\b',r'\bwhy\b',r'\bhow\b',r'\bwhen\b',r'\bwhere\b',
            r'\bexplain\b',r'\btell me\b',r'\bkya\b',r'\bkyon\b',
            r'\bkaise\b',r'\bbatao\b',
        ],
        "anti_patterns": [
            r'\bopen\b',r'\bsend\b',r'\bplay\b',r'\bminimize\b'
        ]
    }
}

def classify(text: str) -> dict:
    """
    Classify user intent from natural language.
    Returns: {intent, confidence, text}
    """
    t      = text.lower().strip()
    scores = {}

    for intent, config in INTENTS.items():
        score = 0
        # Pattern matches
        for pat in config.get("patterns", []):
            if re.search(pat, t):
                score += 1
        # Anti-pattern penalties
        for pat in config.get("anti_patterns", []):
            if re.search(pat, t):
                score -= 2
        if score > 0:
            scores[intent] = score

    if not scores:
        return {"intent": "GENERAL_QA", "confidence": 0.3, "text": text}

    best_intent = max(scores, key=scores.get)
    max_score   = scores[best_intent]
    total       = sum(max(0,v) for v in scores.values()) or 1
    confidence  = min(max_score / total, 1.0)

    return {
        "intent":     best_intent,
        "confidence": round(confidence, 2),
        "text":       text,
        "all_scores": scores
    }