import cv2, os, numpy as np, time

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACE_DIR     = os.path.join(BASE_DIR, "data", "face_data")
TRAINER_FILE = os.path.join(FACE_DIR, "trainer.yml")
os.makedirs(FACE_DIR, exist_ok=True)

def _get_detector():
    # Try multiple paths to find the cascade file
    cascade_paths = [
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml",
        os.path.join(os.path.dirname(cv2.__file__), "data", "haarcascade_frontalface_default.xml"),
        r"C:\ultron\ultron\data\haarcascade_frontalface_default.xml",
    ]
    for path in cascade_paths:
        if os.path.exists(path):
            detector = cv2.CascadeClassifier(path)
            if not detector.empty():
                return detector
    # Download if not found
    _download_cascade()
    local = r"C:\ultron\ultron\data\haarcascade_frontalface_default.xml"
    return cv2.CascadeClassifier(local)

def _download_cascade():
    """Download haarcascade file directly."""
    import urllib.request
    url  = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
    dest = r"C:\ultron\ultron\data\haarcascade_frontalface_default.xml"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        print("[FACE] Downloading haarcascade file...")
        urllib.request.urlretrieve(url, dest)
        print("[FACE] Downloaded successfully.")
    except Exception as e:
        print(f"[FACE] Download error: {e}")

def register_face():
    cap      = cv2.VideoCapture(0)
    detector = _get_detector()
    if detector.empty():
        print("[FACE] ERROR: Could not load face detector.")
        return False
    print("Look at the camera. Taking 5 photos...")
    samples = []; count = 0
    while count < 5:
        ret, frame = cap.read()
        if not ret: break
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)
        for (x,y,w,h) in faces:
            face_img = cv2.resize(gray[y:y+h, x:x+w], (200,200))
            samples.append(face_img)
            count += 1
            print(f"  Photo {count}/5 captured!")
            cv2.waitKey(500)
    cap.release()
    if len(samples) >= 3:
        rec = cv2.face.LBPHFaceRecognizer_create()
        rec.train(samples, np.array([0]*len(samples)))
        rec.save(TRAINER_FILE)
        print("Face registered!")
        return True
    print("Not enough samples. Make sure your face is visible.")
    return False

def is_face_registered():
    return os.path.exists(TRAINER_FILE)

def detect_my_face(timeout=5):
    if not is_face_registered(): return False
    try:
        rec      = cv2.face.LBPHFaceRecognizer_create()
        rec.read(TRAINER_FILE)
        detector = _get_detector()
        if detector.empty(): return False
        cap      = cv2.VideoCapture(0)
        start    = time.time(); found = False
        while time.time() - start < timeout:
            ret, frame = cap.read()
            if not ret: break
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.3, 5)
            for (x,y,w,h) in faces:
                face_img = cv2.resize(gray[y:y+h, x:x+w], (200,200))
                label, conf = rec.predict(face_img)
                if conf < 70: found = True; break
            if found: break
        cap.release()
        return found
    except Exception as e:
        print(f"Face detection error: {e}")
        return False