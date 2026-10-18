import os, sys, shutil, glob, subprocess

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESKTOP   = os.path.join(os.path.expanduser("~"), "Desktop")
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
DOCUMENTS = os.path.join(os.path.expanduser("~"), "Documents")

def _resolve_path(path):
    path = path.strip().strip('"').strip("'")
    path = path.replace("%USERPROFILE%", os.path.expanduser("~"))
    path = path.replace("~/Desktop",    DESKTOP)
    path = path.replace("~/Downloads",  DOWNLOADS)
    path = path.replace("~/Documents",  DOCUMENTS)
    if path.lower() in ["desktop","the desktop","my desktop"]: return DESKTOP
    if path.lower() in ["downloads","my downloads"]:           return DOWNLOADS
    if path.lower() in ["documents","my documents"]:           return DOCUMENTS
    return os.path.expanduser(path)

def create_folder(path):
    try:
        resolved = _resolve_path(path)
        os.makedirs(resolved, exist_ok=True)
        print(f"[FILE] Folder created: {resolved}")
        return os.path.exists(resolved)
    except Exception as e:
        print(f"[FILE] Folder error: {e}"); return False

def create_folder_on_desktop(name):
    path = os.path.join(DESKTOP, name)
    try:
        os.makedirs(path, exist_ok=True)
        print(f"[FILE] Created on Desktop: {path}")
        return os.path.exists(path)
    except Exception as e:
        print(f"[FILE] Desktop folder error: {e}"); return False

def create_file(path, content=""):
    try:
        resolved = _resolve_path(path)
        os.makedirs(os.path.dirname(resolved) if os.path.dirname(resolved) else ".", exist_ok=True)
        with open(resolved, 'w', encoding='utf-8') as f: f.write(content)
        print(f"[FILE] Created: {resolved}"); return True
    except Exception as e:
        print(f"[FILE] Create error: {e}"); return False

def read_file(path):
    try:
        resolved = _resolve_path(path)
        with open(resolved, 'r', encoding='utf-8', errors='ignore') as f: return f.read()
    except Exception as e:
        print(f"[FILE] Read error: {e}"); return ""

def delete_file(path):
    try:
        resolved = _resolve_path(path)
        if os.path.isfile(resolved):  os.remove(resolved)
        elif os.path.isdir(resolved): shutil.rmtree(resolved)
        print(f"[FILE] Deleted: {resolved}"); return True
    except Exception as e:
        print(f"[FILE] Delete error: {e}"); return False

def list_files(path="~"):
    try:
        resolved = _resolve_path(path)
        items    = os.listdir(resolved)
        result   = []
        for item in items[:20]:
            full = os.path.join(resolved, item)
            result.append({"name": item, "type": "folder" if os.path.isdir(full) else "file",
                          "size": os.path.getsize(full) if os.path.isfile(full) else 0})
        return result
    except Exception as e:
        print(f"[FILE] List error: {e}"); return []

def copy_file(src, dst):
    try:
        s = _resolve_path(src); d = _resolve_path(dst)
        os.makedirs(os.path.dirname(d) if os.path.dirname(d) else ".", exist_ok=True)
        shutil.copy2(s, d); return True
    except Exception as e:
        print(f"[FILE] Copy error: {e}"); return False

def move_file(src, dst):
    try:
        s = _resolve_path(src); d = _resolve_path(dst)
        os.makedirs(os.path.dirname(d) if os.path.dirname(d) else ".", exist_ok=True)
        shutil.move(s, d); return True
    except Exception as e:
        print(f"[FILE] Move error: {e}"); return False

def find_file(name, search_dirs=None):
    if not search_dirs: search_dirs = [DESKTOP, DOWNLOADS, DOCUMENTS]
    found = []
    for d in search_dirs:
        try: found.extend(glob.glob(os.path.join(d, f"**/*{name}*"), recursive=True)[:5])
        except: pass
    return found[:10]

def run_command(cmd):
    try:
        result = subprocess.run(["powershell", "-Command", cmd],
                               capture_output=True, text=True, timeout=60)
        return result.stdout.strip() or result.stderr.strip()
    except Exception as e: return str(e)

def organize_downloads():
    categories = {
        "Images":    [".jpg",".jpeg",".png",".gif",".bmp",".webp",".svg"],
        "Videos":    [".mp4",".avi",".mkv",".mov",".wmv",".flv"],
        "Audio":     [".mp3",".wav",".flac",".aac",".ogg"],
        "Documents": [".pdf",".doc",".docx",".txt",".xls",".xlsx",".ppt",".pptx"],
        "Archives":  [".zip",".rar",".7z",".tar",".gz"],
        "Code":      [".py",".js",".html",".css",".java",".cpp",".c",".ts"],
        "Installers":[".exe",".msi"],
    }
    moved = {}
    for fname in os.listdir(DOWNLOADS):
        fpath = os.path.join(DOWNLOADS, fname)
        if os.path.isfile(fpath):
            ext = os.path.splitext(fname)[1].lower()
            for category, exts in categories.items():
                if ext in exts:
                    dest_dir = os.path.join(DOWNLOADS, category)
                    os.makedirs(dest_dir, exist_ok=True)
                    dest = os.path.join(dest_dir, fname)
                    if not os.path.exists(dest):
                        shutil.move(fpath, dest)
                        moved[fname] = category
                    break
    return moved