import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

_hud      = None
_launcher = None

def register_hud(hud_instance):
    global _hud
    _hud = hud_instance

def register_launcher(launcher_instance):
    global _launcher
    _launcher = launcher_instance

def set_state(state: str):
    if _hud:
        try: _hud.set_state(state)
        except: pass

def set_command(cmd: str):
    if _hud:
        try: _hud.set_command(cmd)
        except: pass

def set_heard(text: str):
    if _hud:
        try: _hud.set_heard(text)
        except: pass

def set_response(text: str):
    if _hud:
        try: _hud.set_response(text)
        except: pass

def notify(text: str):
    if _hud:
        try: _hud.add_notification(text)
        except: pass

def set_speaking(is_speaking: bool):
    set_state("SPEAKING" if is_speaking else "ONLINE")

def show_launcher():
    if _launcher:
        try: _launcher.show_launcher()
        except: pass

def hide_launcher():
    if _launcher:
        try: _launcher.hide_launcher()
        except: pass