"""
vision.py â€” backward compatibility wrapper
Routes to vision_system modules
"""
import os, sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import pytesseract
from PIL import ImageGrab, Image
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def _clean(text):
    import re
    return text.encode('ascii',errors='ignore').decode('ascii').strip()

def _ask_groq(prompt):
    GROQ_API_KEY = ""
    try:
        with open(os.path.join(BASE_DIR,"config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"system","content":"You are ULTRON. Analyze content concisely. Address as Sparsh Sir. Max 3 sentences."},
                      {"role":"user","content":prompt}],
            max_tokens=200, temperature=0.5)
        return response.choices[0].message.content.strip()
    except Exception as e: return f"Analysis error: {e}"

def read_screen():
    try:
        text = _clean(pytesseract.image_to_string(ImageGrab.grab(),lang='eng'))
        if len(text) < 20: return "I can see your screen Sir but there is not much readable text on it."
        return _ask_groq(f"Text from screen:\n\n{text[:1500]}\n\nSummarize what user is doing. Address as Sparsh Sir.")
    except Exception as e: return f"Could not read screen Sir. Error: {e}"

def read_pdf(file_path=None):
    try:
        import fitz, glob
        if not file_path:
            pdfs=[]
            for d in ["Desktop","Downloads","Documents"]:
                pdfs.extend(glob.glob(os.path.join(os.path.expanduser("~"),d,"*.pdf")))
            if not pdfs: return "No PDF files found Sir."
            file_path=max(pdfs,key=os.path.getmtime)
        doc=fitz.open(file_path)
        text=_clean("".join([doc[i].get_text() for i in range(min(5,len(doc)))]))[:2000]
        doc.close()
        if not text: return "PDF appears empty Sir."
        return _ask_groq(f"PDF '{os.path.basename(file_path)}':\n\n{text}\n\nSummarize. Address as Sparsh Sir.")
    except Exception as e: return f"Could not read PDF Sir. Error: {e}"

def analyze_image(file_path=None):
    try:
        import glob
        if not file_path:
            images=[]
            for d in ["Desktop","Downloads","Pictures"]:
                for ext in ['*.jpg','*.jpeg','*.png','*.bmp']:
                    images.extend(glob.glob(os.path.join(os.path.expanduser("~"),d,ext)))
            if not images: return "No images found Sir."
            file_path=max(images,key=os.path.getmtime)
        img=Image.open(file_path); text=_clean(pytesseract.image_to_string(img))
        fname=os.path.basename(file_path)
        prompt=(f"Image '{fname}' text:\n{text}\nDescribe. Address as Sparsh Sir." if text and len(text)>10
                else f"Image '{fname}' no text. Guess from filename. Address as Sparsh Sir.")
        return _ask_groq(prompt)
    except Exception as e: return f"Could not analyze image Sir. Error: {e}"

def look_through_camera():
    try:
        import cv2, tempfile
        cap=cv2.VideoCapture(0)
        if not cap.isOpened(): return "Camera not available Sir."
        for _ in range(5): ret,frame=cap.read()
        cap.release()
        if not ret: return "Could not capture from camera Sir."
        tmp=tempfile.mktemp(suffix='.jpg')
        cv2.imwrite(tmp,frame)
        text=_clean(pytesseract.image_to_string(Image.open(tmp)))
        try: os.remove(tmp)
        except: pass
        return _ask_groq(f"Camera text:\n{text}\nDescribe surroundings. Address as Sparsh Sir." if text and len(text)>10
                        else "Camera working but no text visible. Tell Sparsh Sir briefly.")
    except Exception as e: return f"Camera error Sir: {e}"

def describe_screenshot():
    try:
        text=_clean(pytesseract.image_to_string(ImageGrab.grab()))
        if not text: return "Screen is mostly visual Sir. No readable text detected."
        return _ask_groq(f"Screen:\n\n{text[:1500]}\n\nTell Sparsh Sir what is on screen.")
    except Exception as e: return f"Could not scan screen Sir. Error: {e}"
