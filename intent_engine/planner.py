"""
planner.py
Creates execution plans from intents.
User never needs to specify intermediate steps.
"""
import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def plan(intent: str, entities: dict, context: dict = None) -> list:
    """
    Create step-by-step execution plan from intent + entities.
    Returns list of action steps.
    """
    ctx = context or {}

    if intent == "OPEN_APP":
        return _plan_open_app(entities, ctx)
    elif intent == "CLOSE_APP":
        return _plan_close_app(entities, ctx)
    elif intent == "OPEN_WEBSITE":
        return _plan_open_website(entities, ctx)
    elif intent == "SEND_MESSAGE":
        return _plan_send_message(entities, ctx)
    elif intent == "WINDOW_ACTION":
        return _plan_window_action(entities, ctx)
    elif intent == "SCREEN_CONTEXT":
        return [{"action":"get_screen_context","params":{}}]
    elif intent == "CONTINUE_WORK":
        return _plan_continue_work(entities, ctx)
    elif intent == "SEARCH_WEB":
        return _plan_search_web(entities, ctx)
    elif intent == "PLAY_MEDIA":
        return _plan_play_media(entities, ctx)
    elif intent == "GAMING_MODE":
        return [{"action":"start_gaming_mode","params":{"game":"asphalt"}}]
    elif intent == "SYSTEM_INFO":
        return [{"action":"get_system_info","params":{}}]
    elif intent == "TAKE_NOTE":
        return [{"action":"take_note","params":{"text":entities.get("raw","")}}]
    else:
        return [{"action":"llm_answer","params":{"query":entities.get("raw","")}}]

def _plan_open_app(entities, ctx):
    app = entities.get("app","")
    if not app:
        website = entities.get("website","")
        if website:
            return _plan_open_website(entities, ctx)
        return [{"action":"llm_answer","params":{"query":"What app to open?"}}]
    steps = [
        {"action":"check_app_running","params":{"app":app}},
        {"action":"launch_app","params":{"app":app},"on_already_running":"focus_app"},
        {"action":"verify_app_open","params":{"app":app}},
    ]
    return steps

def _plan_close_app(entities, ctx):
    app = entities.get("app","") or entities.get("window_target","")
    if not app: return [{"action":"llm_answer","params":{"query":"Which app to close?"}}]
    return [
        {"action":"close_app","params":{"app":app}},
        {"action":"speak","params":{"text":f"{app.title()} closed Sir."}}
    ]

def _plan_open_website(entities, ctx):
    site = entities.get("website","") or entities.get("app","")
    if not site: return [{"action":"llm_answer","params":{"query":"Which website to open?"}}]
    return [
        {"action":"check_website_open","params":{"site":site}},
        {"action":"open_website","params":{"site":site},"on_already_open":"focus_tab"},
        {"action":"speak","params":{"text":f"Opening {site.title()} Sir."}}
    ]

def _plan_send_message(entities, ctx):
    recipient = entities.get("recipient","")
    message   = entities.get("message","")
    platform  = entities.get("platform","whatsapp")

    if not recipient:
        return [{"action":"ask_user","params":{"question":"Who should I message Sir?"}}]

    steps = [
        {"action":"open_platform","params":{"platform":platform}},
        {"action":"search_contact","params":{"contact":recipient}},
        {"action":"open_chat","params":{"contact":recipient}},
    ]

    if message:
        steps += [
            {"action":"confirm_send","params":{"contact":recipient,"message":message}},
            {"action":"type_message","params":{"message":message}},
            {"action":"send_message","params":{}},
            {"action":"speak","params":{"text":f"Message sent to {recipient} Sir."}}
        ]
    else:
        steps.append({"action":"ask_user","params":{"question":"What message shall I send?"}})

    return steps

def _plan_window_action(entities, ctx):
    action = entities.get("window_action","focus")
    target = entities.get("window_target","") or entities.get("app","")
    if not target:
        return [{"action":"llm_answer","params":{"query":"Which window?"}}]
    return [
        {"action":"window_action","params":{"action":action,"target":target}},
        {"action":"speak","params":{"text":f"{target.title()} {action}d Sir."}}
    ]

def _plan_continue_work(entities, ctx):
    time_ref = entities.get("time_ref","yesterday")
    project  = entities.get("project","")
    return [
        {"action":"load_last_session","params":{"time_ref":time_ref,"project":project}},
        {"action":"restore_workspace","params":{}},
        {"action":"summarize_session","params":{}},
    ]

def _plan_search_web(entities, ctx):
    query = entities.get("query","")
    if not query: return [{"action":"llm_answer","params":{"query":"Search for what?"}}]
    return [
        {"action":"open_website","params":{"site":f"https://www.google.com/search?q={query}"}},
        {"action":"speak","params":{"text":f"Searching for {query} Sir."}}
    ]

def _plan_play_media(entities, ctx):
    query = entities.get("query","") or entities.get("raw","")
    return [
        {"action":"open_website","params":{"site":f"https://www.youtube.com/results?search_query={query}"}},
        {"action":"speak","params":{"text":f"Playing {query} Sir."}}
    ]