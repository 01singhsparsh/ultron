STRESS_WORDS = ["stressed","stress","tired","exhausted","frustrated","annoyed",
    "angry","upset","worried","anxious","help","emergency",
    "not working","broke","error","problem","stuck","confused",
    "cant","cannot","failing","failed","worst","hate"]
HAPPY_WORDS  = ["great","awesome","amazing","excellent","fantastic","wonderful",
    "happy","excited","good","nice","cool","love","perfect","brilliant",
    "thanks","thank you","well done","yes","yay","wow"]
TIRED_WORDS  = ["tired","sleepy","sleep","rest","exhausted","bored","nap","bed","night"]

_current_mood = "neutral"

def detect_mood(text):
    global _current_mood
    t = text.lower()
    if any(w in t for w in STRESS_WORDS):  _current_mood = "stressed"
    elif any(w in t for w in TIRED_WORDS): _current_mood = "tired"
    elif any(w in t for w in HAPPY_WORDS): _current_mood = "happy"
    else:                                  _current_mood = "neutral"
    return _current_mood

def get_mood(): return _current_mood

def get_mood_response_prefix():
    if _current_mood == "stressed": return "I can sense you might be under pressure Sir. "
    elif _current_mood == "tired":  return "You sound tired Sir. "
    elif _current_mood == "happy":  return "Glad to hear you are in good spirits Sir. "
    return ""