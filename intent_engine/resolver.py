"""
resolver.py
Main entry point for the Intent Engine.
Takes raw user text → classifies → extracts → plans → executes.
"""
import os, sys, time
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from intent_engine.classifier      import classify
from intent_engine.entity_extractor import extract_entities
from intent_engine.planner          import plan
from intent_engine.executor_bridge  import execute_plan

# Intents that should NOT go through intent engine
# (let existing handlers deal with them)
SKIP_INTENTS = {"GENERAL_QA"}

def resolve(text: str) -> dict:
    """
    Full pipeline: text → intent → entities → plan → execute.
    Returns: {handled, success, response, intent}
    """
    start = time.time()

    # Step 1 — Classify
    classification = classify(text)
    intent         = classification["intent"]
    confidence     = classification["confidence"]

    print(f"[INTENT] '{text}' → {intent} ({confidence:.2f})")

    # Low confidence or general QA — let LLM handle it
    if intent in SKIP_INTENTS or confidence < 0.25:
        return {"handled": False, "intent": intent}

    # Step 2 — Extract entities
    entities        = extract_entities(text, intent)
    entities["raw"] = text
    print(f"[INTENT] Entities: {entities}")

    # Step 3 — Plan
    steps = plan(intent, entities)
    print(f"[INTENT] Plan: {len(steps)} steps")

    # Step 4 — Execute
    result = execute_plan(steps, text)

    elapsed = round(time.time() - start, 2)
    print(f"[INTENT] Completed in {elapsed}s")

    # Log to session
    try:
        from context_engine.session_manager import log_activity
        log_activity(f"Intent: {intent} — {text[:60]}", category="command")
    except: pass

    return {
        "handled":  True,
        "success":  result.get("success", True),
        "response": result.get("response",""),
        "intent":   intent,
        "elapsed":  elapsed,
    }

def should_use_intent_engine(text: str) -> bool:
    """Quick check if text should go through intent engine."""
    t = text.lower().strip()
    # Remove wake words
    for w in ["ultron","hey ultron","hello ultron"]:
        t = t.replace(w,"").strip()

    # Minimum length
    if len(t) < 3: return False

    # Quick pattern check
    action_words = [
        "open","close","launch","send","message","minimize","maximize",
        "search","play","start","switch","go to","continue","restore",
        "khol","band","bhej","chal","shuru","message karo",
    ]
    return any(w in t for w in action_words)