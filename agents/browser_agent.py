import time, os, webbrowser

_driver = None

def _get_driver():
    global _driver
    if _driver is not None:
        try: _ = _driver.current_url; return _driver
        except: _driver = None
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_experimental_option("excludeSwitches",["enable-logging"])
        service = Service(ChromeDriverManager().install())
        _driver = webdriver.Chrome(service=service, options=options)
        print("[BROWSER] Chrome driver initialized")
        return _driver
    except Exception as e:
        print(f"[BROWSER] Driver error: {e}"); return None

def open_url(url):
    if not url.startswith("http"): url = "https://" + url
    print(f"[BROWSER] Opening: {url}")
    try:
        driver = _get_driver()
        if driver: driver.get(url); time.sleep(2); return True
        else: webbrowser.open(url); return True
    except:
        webbrowser.open(url); return True

def search_web(query):
    import urllib.parse
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    return open_url(url)

def download_file(url, save_path):
    try:
        import urllib.request
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        urllib.request.urlretrieve(url, save_path)
        print(f"[BROWSER] Downloaded to: {save_path}"); return True
    except Exception as e:
        print(f"[BROWSER] Download error: {e}"); return False

def close_browser():
    global _driver
    try:
        if _driver: _driver.quit(); _driver = None
    except: pass