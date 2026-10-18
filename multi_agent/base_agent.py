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

class BaseAgent:
    def __init__(self, name, role, max_tokens=500):
        self.name       = name
        self.role       = role
        self.max_tokens = max_tokens
        self.history    = []
        print(f"[{self.name}] Initialized")

    def think(self, prompt, system=None):
        if not GROQ_API_KEY: return "No API key configured."
        try:
            from groq import Groq
            client   = Groq(api_key=GROQ_API_KEY)
            messages = []
            if system: messages.append({"role":"system","content":system})
            for h in self.history[-4:]: messages.append(h)
            messages.append({"role":"user","content":prompt})
            response = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=messages, max_tokens=self.max_tokens, temperature=0.3)
            reply = response.choices[0].message.content.strip()
            self.history.append({"role":"user","content":prompt})
            self.history.append({"role":"assistant","content":reply})
            if len(self.history) > 10: self.history = self.history[-10:]
            return reply
        except Exception as e:
            print(f"[{self.name}] Think error: {e}"); return f"Error: {e}"

    def think_json(self, prompt, system=None):
        json_system = (system or "") + "\nReturn ONLY valid JSON. No extra text."
        raw = self.think(prompt, json_system)
        try:
            start = raw.find("{"); end = raw.rfind("}") + 1
            if start != -1 and end > start: return json.loads(raw[start:end])
            start = raw.find("["); end = raw.rfind("]") + 1
            if start != -1 and end > start: return json.loads(raw[start:end])
        except: pass
        return {}

    def run(self, task, context=None):
        raise NotImplementedError

    def log(self, msg):
        print(f"[{self.name}] {msg}")

