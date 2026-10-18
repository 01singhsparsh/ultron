import os, sys, re
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

ERROR_PATTERNS = {
    "python":  [r'Traceback \(most recent call last\)',r'(SyntaxError|NameError|TypeError|ValueError|ImportError|AttributeError)',r'Error: .+',r'ModuleNotFoundError'],
    "windows": [r'(Error|error) code: \d+',r'Windows cannot',r'Access is denied',r'has stopped working'],
    "browser": [r'404 Not Found',r'500 Internal Server Error',r'ERR_',r'This site can\'t be reached'],
    "network": [r'Connection refused',r'Connection timed out',r'No internet',r'DNS_PROBE'],
}

def detect_error_type(text):
    detected = []
    for error_type, patterns in ERROR_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE): detected.append(error_type); break
    if not detected and any(w in text.lower() for w in ['error','fail','crash','exception']): detected.append("generic")
    return {"has_error":len(detected)>0,"error_types":detected,"primary":detected[0] if detected else None}

def extract_error_message(text):
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if 'Traceback' in line: return '\n'.join(lines[i:i+20])
    error_lines = [l for l in lines if re.search(r'(Error|Exception|Warning|FAILED)', l, re.IGNORECASE)]
    return '\n'.join(error_lines[:10]) if error_lines else text[:500]

def explain_error(error_text):
    if not GROQ_API_KEY: return "No API key configured."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {"role":"system","content":"You are ULTRON, an expert debugger. Explain errors in simple terms and provide exact fix steps. Address as Sparsh Sir. Max 3 sentences."},
                {"role":"user","content":f"Explain this error and how to fix it:\n{error_text[:1000]}"}
            ], max_tokens=200, temperature=0.2)
        return response.choices[0].message.content.strip()
    except Exception as e: return f"Error analysis failed: {e}"

def suggest_fix(error_text, context=""):
    if not GROQ_API_KEY: return ""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {"role":"system","content":"You are ULTRON's debugging engine. Provide the exact fix for the error. Be direct and specific. Address as Sparsh Sir."},
                {"role":"user","content":f"Error:\n{error_text[:800]}\nContext: {context[:200]}\nProvide exact fix:"}
            ], max_tokens=300, temperature=0.2)
        return response.choices[0].message.content.strip()
    except Exception as e: return f"Fix suggestion failed: {e}"

def analyze_screen_for_errors():
    try:
        from vision_system.ocr_engine import get_screen_text
        screen_text = get_screen_text()
        detection   = detect_error_type(screen_text)
        if not detection["has_error"]:
            return {"has_error":False,"message":"No errors detected on screen Sir.","screen_text":screen_text[:500]}
        error_msg   = extract_error_message(screen_text)
        explanation = explain_error(error_msg)
        fix         = suggest_fix(error_msg)
        return {"has_error":True,"error_types":detection["error_types"],"error_msg":error_msg[:300],
                "explanation":explanation,"fix":fix,"screen_text":screen_text[:500]}
    except Exception as e:
        return {"has_error":False,"message":f"Analysis error: {e}"}
