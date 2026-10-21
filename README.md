<div align="center">

# ULTRON OS

### A voice-controlled personal AI desktop assistant for Windows

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![LLM](https://img.shields.io/badge/LLM-Groq-F55036?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-00C853?style=for-the-badge)

*"Good evening Sir. Ultron online and ready."*

</div>

---

## What is ULTRON?

ULTRON is a personal AI operating layer that sits on top of Windows. You talk to it, and it opens apps, controls windows, remembers things, reads your screen, plans multi-step tasks, builds small software projects, and even lets you fly around a 3D Earth with your hands.

It started as a portfolio project and grew into a modular system: a voice pipeline, an intent engine, a desktop agent, a multi-agent brain, long-term memory, computer vision, gesture control and a holographic HUD - all in Python.

## Features

| Module | What it does | Folder |
|---|---|---|
| **Voice and intent engine** | Listens, classifies what you said, extracts entities, resolves them and plans the action | `intent_engine/`, `modules/` |
| **Desktop agent** | Launches apps and websites, manages windows, controls WhatsApp, routes commands | `agents/`, `executor/` |
| **Holographic HUD** | Always-on overlay and floating app launcher (PyQt6 + Win32) | `hud/` |
| **Memory engine** | Episodic memory (SQLite) and semantic memory (ChromaDB), plus a personality layer | `memory/` |
| **Second Brain** | RAG over your own documents: ingestion, vector store, retrieval | `second_brain/` |
| **Multi-agent system** | Orchestrator with six specialists: planner, research, coding, critic, executor, memory | `multi_agent/` |
| **Vision system** | Screen capture, OCR, screen analysis and error detection | `vision_system/` |
| **Project builder** | Plans, generates, runs and debugs multi-file projects autonomously | `project_builder/` |
| **Hands-free mode** | Control the cursor with hand gestures (MediaPipe) | `hands_free/` |
| **Gaming mode** | Game detection, launcher, copilot and a gesture-driven wheel | `gaming_mode/` |
| **Pipeline mode** | Experimental hand-tracked workspace with a physics engine and renderer | `pipeline/` |
| **Earth mode** | 3D solar system, rotatable globe and satellite map, driven by voice and gestures | `earth_mode/` |
| **Proactive monitoring** | Background awareness, session recording, context engine | `proactive.py`, `context_engine/` |

## How it fits together

~~~
 Microphone -> listener -> intent_engine
                 (classify -> extract entities -> resolve -> plan)
                              |
        +---------------------+------------------------+
        v                     v                        v
  Desktop agent        Multi-agent system        Special modes
  apps, windows,       planner, research,        Earth, Gaming, Pipeline,
  browser, files       coding, critic ...        Hands-free
        |                     |                        |
        +------ Memory (SQLite + ChromaDB)  /  Second Brain (RAG) ------+
                              |
                  Speaker (TTS)  +  Holographic HUD
~~~

## Earth Mode

> **Standalone repo:** Earth Mode also lives on its own - [01singhsparsh/ultron-earth-mode](https://github.com/01singhsparsh/ultron-earth-mode) - run it without the rest of ULTRON.

Say **"show me Earth mode"** and a browser opens a real-time 3D scene (Three.js): the solar system, then a NASA Blue Marble globe, then a Leaflet/Esri satellite map when you zoom in far enough.

**Voice commands**

| Say | What happens |
|---|---|
| "show me Earth mode" | Opens Earth Mode |
| "show me Taj Mahal" / "take me to Paris" | Flies to the place |
| "I am at Chandigarh University" | Sets your location, centres the view there, then leaves you free to move |
| "show me directions" | Draws a direction arrow and distance from your location to the last place you visited |
| "where am I" | Refreshes your live location |
| "satellite view" / "night mode" / "reset view" | Switches layer or resets the camera |
| "close Earth mode" | Exits |

**Hand gestures** (webcam, runs in the browser with MediaPipe)

| Gesture | Globe view | Map view |
|---|---|---|
| Move one open hand | Rotate the globe | Pan the map |
| Open your fingers | Zoom in | Zoom out |
| Close your fist | Zoom out | Zoom in |
| Two hands apart | Zoom in | Zoom out |
| Two hands together | Zoom out | Zoom in |
| One finger | Point at a place (shows coordinates) | Point at a place |
| Two fingers | Mark the place and show direction from you | Same |

> Browser geolocation on a laptop without GPS can be tens of kilometres off. Say "I am at <your place>" to set it exactly.

## Getting started

**Requirements:** Windows 10/11, Python 3.11, a microphone, and optionally a webcam for gestures.

~~~powershell
# 1. Clone
git clone https://github.com/01singhsparsh/ultron.git
cd ultron

# 2. Install the core packages (a full requirements.txt is on the roadmap)
py -3.11 -m pip install groq PyQt6 opencv-contrib-python mediapipe==0.10.9 pyttsx3 chromadb
# ...plus the speech-recognition / audio packages imported by modules/listener.py

# 3. Add your Groq API key
copy config.example.py config.py
notepad config.py        # replace PASTE_YOUR_KEY_HERE with your key from https://console.groq.com/keys

# 4. Run
py -3.11 ultron.py
~~~

Then say **"Hello Ultron"**.

## Security

- Your API key lives only in `config.py`, which is git-ignored and never uploaded. `config.example.py` is the safe template.
- Runtime data (`data/`), conversation logs and memory databases stay on your machine.
- Never commit a real key. If you ever do, revoke it immediately in the Groq console.

## Roadmap

- [ ] `requirements.txt` and a one-command installer
- [ ] Screenshots and a demo video
- [ ] Automated tests for the intent engine
- [ ] Earth Mode: "take me to my location" fly-to
- [ ] Packaged Windows installer

## Author

Built by **Sparsh Singh** - [@01singhsparsh](https://github.com/01singhsparsh)