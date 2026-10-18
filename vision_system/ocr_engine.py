import os, re
import pytesseract
from PIL import Image, ImageGrab, ImageEnhance, ImageFilter
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def _preprocess_image(img):
    img = img.convert('L')
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    return img

def capture_screen(): return ImageGrab.grab()

def extract_text_tesseract(img=None):
    try:
        if img is None: img = capture_screen()
        processed = _preprocess_image(img)
        text      = pytesseract.image_to_string(processed, config='--psm 6 --oem 3')
        return _clean(text)
    except Exception as e:
        print(f"[OCR] Tesseract error: {e}"); return ""

def extract_text(img=None, use_easyocr=False):
    if use_easyocr:
        try:
            import easyocr
            if img is None: img = capture_screen()
            reader  = easyocr.Reader(['en'], verbose=False)
            results = reader.readtext(np.array(img))
            return _clean("\n".join([r[1] for r in results if r[2] > 0.3]))
        except: pass
    return extract_text_tesseract(img)

def extract_text_from_region(x1, y1, x2, y2):
    try: return extract_text(ImageGrab.grab(bbox=(x1,y1,x2,y2)))
    except Exception as e: print(f"[OCR] Region error: {e}"); return ""

def extract_from_image_file(path):
    try: return extract_text(Image.open(path))
    except Exception as e: print(f"[OCR] File error: {e}"); return ""

def get_screen_text():   return extract_text()
def find_text_on_screen(search): return search.lower() in get_screen_text().lower()

def _clean(text):
    text = text.encode('ascii', errors='ignore').decode('ascii')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()