"""
hands_free_patch_for_ultron.py

HOW TO INTEGRATE INTO ultron.py:
=================================
In your ultron.py, inside the main voice command handler function
(the one that processes the recognized text), add this EARLY CHECK:

    # ── Hands-Free Mode (add near top of command handler) ──
    from hands_free.voice_integration import handle_hands_free_command
    if handle_hands_free_command(text):
        return  # command handled

This single line routes all hands-free voice commands.

EXAMPLE - find your handle_command or process_command function and add:
=========================================================================

def handle_command(text: str):
    # ── Hands-Free Mode early intercept ──
    try:
        from hands_free.voice_integration import handle_hands_free_command
        if handle_hands_free_command(text):
            return
    except Exception as e:
        print(f"[HANDS-FREE] Voice integration error: {e}")

    # ... rest of your existing command handling ...

EMERGENCY STOP HOTKEY (optional):
===================================
Add this anywhere at startup:

    try:
        import keyboard
        def _emergency_hotkey():
            from hands_free.hands_free_manager import HandsFreeManager
            HandsFreeManager.get_instance().emergency_stop()
        keyboard.add_hotkey("escape", _emergency_hotkey)
    except ImportError:
        pass
"""

# This file is documentation-only. No executable code.
print("Read the docstring above for integration instructions.")
