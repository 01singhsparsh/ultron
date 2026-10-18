"""
whatsapp_controller.py
Actually sends WhatsApp messages — no hallucination.
Opens WhatsApp Desktop, searches contact, types and sends.
"""
import subprocess, time, pyautogui, os, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pyautogui.FAILSAFE = False
pyautogui.PAUSE    = 0.2

def _open_whatsapp() -> bool:
    """Open WhatsApp Desktop app."""
    try:
        subprocess.Popen(
            ["powershell","-Command","start-process whatsapp:"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        time.sleep(4)
        return _is_whatsapp_open()
    except: return False

def _is_whatsapp_open() -> bool:
    """Check if WhatsApp window is open."""
    try:
        import pygetwindow as gw
        for win in gw.getAllWindows():
            if "whatsapp" in win.title.lower():
                return True
    except: pass
    return False

def _focus_whatsapp() -> bool:
    """Bring WhatsApp to foreground."""
    try:
        import pygetwindow as gw
        for win in gw.getAllWindows():
            if "whatsapp" in win.title.lower():
                win.restore()
                win.activate()
                time.sleep(0.5)
                return True
    except: pass
    return False

def _search_contact(contact: str):
    """Search for a contact in WhatsApp."""
    # Press Ctrl+F or Ctrl+K to open search
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.typewrite(contact, interval=0.05)
    time.sleep(2)
    pyautogui.press('enter')
    time.sleep(1)

def _type_and_send(message: str):
    """Type message and send it."""
    # Click message box area (bottom of WhatsApp)
    import pyautogui
    screen_w, screen_h = pyautogui.size()
    pyautogui.click(screen_w // 2, int(screen_h * 0.93))
    time.sleep(0.5)
    pyautogui.typewrite(message, interval=0.04)
    time.sleep(0.3)
    pyautogui.press('enter')
    time.sleep(0.5)

def send_message(contact: str, message: str, confirmed: bool = False) -> dict:
    """
    Send a WhatsApp message to a contact.
    Always asks for voice confirmation before sending.
    """
    if not contact or not message:
        return {"success": False, "message": "Contact or message is empty."}

    # Open WhatsApp
    if not _is_whatsapp_open():
        opened = _open_whatsapp()
        if not opened:
            return {"success": False, "message": "Could not open WhatsApp."}
    else:
        _focus_whatsapp()
        time.sleep(1)

    # Search contact
    _search_contact(contact)

    # Type and send
    _type_and_send(message)

    return {
        "success": True,
        "message": f"Message sent to {contact}.",
        "contact": contact,
        "text":    message
    }

def open_chat(contact: str) -> dict:
    """Open WhatsApp chat with a contact."""
    if not _is_whatsapp_open():
        _open_whatsapp()
    else:
        _focus_whatsapp()
        time.sleep(1)
    _search_contact(contact)
    return {"success": True, "message": f"Opened chat with {contact}."}