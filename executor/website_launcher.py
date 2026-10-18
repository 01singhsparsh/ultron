"""
website_launcher.py
Opens websites in the default browser.
Resolves aliases so "open chatgpt" works.
"""
import json, os, webbrowser

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIAS_FILE = os.path.join(BASE_DIR, "executor", "alias_database.json")

def _load_aliases() -> dict:
    try:
        with open(ALIAS_FILE) as f:
            return json.load(f).get("websites", {})
    except: return {}

def _resolve_url(name: str) -> str:
    """Resolve a name to a URL."""
    aliases   = _load_aliases()
    name_lower= name.lower().strip()

    # Direct match
    if name_lower in aliases:
        return aliases[name_lower]

    # Partial match
    for key, url in aliases.items():
        if key in name_lower or name_lower in key:
            return url

    # Already a URL
    if "." in name and " " not in name:
        if not name.startswith("http"):
            return "https://" + name
        return name

    # Search Google as fallback
    import urllib.parse
    return f"https://www.google.com/search?q={urllib.parse.quote(name)}"

def open_website(name: str) -> dict:
    """Open a website by name or URL."""
    url = _resolve_url(name)
    try:
        webbrowser.open(url)
        display = name.title() if not name.startswith("http") else url
        return {
            "success": True,
            "url":     url,
            "message": f"Opening {display} Sir."
        }
    except Exception as e:
        return {
            "success": False,
            "url":     url,
            "message": f"Could not open {name}. Error: {e}"
        }

def get_website_url(name: str) -> str:
    return _resolve_url(name)