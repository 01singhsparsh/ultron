import speech_recognition as sr
import os, time, socket

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

r = sr.Recognizer()
r.energy_threshold         = 300
r.dynamic_energy_threshold = False
r.pause_threshold          = 0.5
r.phrase_threshold         = 0.2
r.non_speaking_duration    = 0.3

def _internet_ok() -> bool:
    """Quick check if internet is reachable."""
    try:
        socket.setdefaulttimeout(2)
        socket.create_connection(("8.8.8.8", 53))
        return True
    except OSError:
        return False

def listen(timeout=4, phrase_limit=6):
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.1)
            try:
                audio = r.listen(
                    source,
                    timeout           = timeout,
                    phrase_time_limit = phrase_limit
                )
            except sr.WaitTimeoutError:
                return None

        # If no internet skip Google and return None silently
        if not _internet_ok():
            return None

        # Google Speech Recognition
        try:
            text = r.recognize_google(audio, language="en-IN").strip()
            if text:
                print(f"[MIC] Heard: {text}")
                return text
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            # Network failed — try again once after short wait
            time.sleep(0.5)
            try:
                text = r.recognize_google(audio, language="en-IN").strip()
                if text:
                    print(f"[MIC] Heard: {text}")
                    return text
            except Exception:
                pass
            return None

    except OSError as e:
        if "getaddrinfo" in str(e) or "connection" in str(e).lower():
            pass  # Silent — no internet yet
        else:
            print(f"[LISTEN] Error: {e}")
        return None
    except Exception as e:
        print(f"[LISTEN] Error: {e}")
        return None