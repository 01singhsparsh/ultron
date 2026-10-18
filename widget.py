"""
widget.py
ULTRON Desktop Companion — Avengers Age of Ultron inspired.
Click to wake. Silent. Always on top.
"""
import sys, os, subprocess, threading, math, time, json, random
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
ULTRON_PATH = os.path.join(BASE_DIR, "ultron.py")
POS_FILE    = os.path.join(BASE_DIR, "data", "companion_pos.json")
SIGNAL_FILE = os.path.join(BASE_DIR, "data", "wake_signal.txt")
PYTHON      = r"C:\Users\ASUS\AppData\Local\Programs\Python\Python311\python.exe"
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

from PyQt6.QtWidgets import (QApplication, QWidget, QMenu, QSystemTrayIcon)
from PyQt6.QtCore    import (Qt, QPoint, QTimer, QPointF, QRectF)
from PyQt6.QtGui     import (QPainter, QColor, QBrush, QPen, QFont,
                              QIcon, QPixmap, QRadialGradient)

STATE_IDLE      = "idle"
STATE_HOVER     = "hover"
STATE_LISTENING = "listening"
STATE_THINKING  = "thinking"
STATE_SPEAKING  = "speaking"
STATE_BOOTING   = "booting"

class UltronCompanion(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(140, 140)

        self.state        = STATE_BOOTING
        self.ultron_proc  = None
        self.is_running   = False
        self.drag_pos     = QPoint()
        self.is_dragging  = False

        self.t              = 0.0
        self.boot_alpha     = 0.0
        self.pulse          = 0.0
        self.pulse_dir      = 1
        self.ring_angle     = 0.0
        self.energy_angle   = 0.0
        self.wave_phase     = 0.0
        self.hover_scale    = 1.0
        self.target_scale   = 1.0
        self.glow_intensity = 0.5
        self.speak_bars     = [0.0] * 8

        self.orbitals = [
            {'angle': random.uniform(0, 2*math.pi),
             'speed': random.uniform(0.015, 0.04),
             'r':     random.uniform(52, 68),
             'size':  random.uniform(2, 4),
             'phase': random.uniform(0, 2*math.pi)}
            for _ in range(18)
        ]

        self._load_position()

        self.boot_timer = QTimer()
        self.boot_timer.timeout.connect(self._boot_tick)
        self.boot_timer.start(16)

        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self._tick)
        self.main_timer.start(33)

        self._setup_tray()
        self.show()

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        pix = QPixmap(32, 32)
        pix.fill(QColor(0, 0, 0, 0))
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(0, 180, 210)))
        p.setPen(QPen(QColor(0, 220, 240), 1))
        p.drawEllipse(3, 3, 26, 26)
        p.end()
        self.tray.setIcon(QIcon(pix))
        self.tray.setToolTip("ULTRON OS")
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background:#000d0f; color:#00d4e8; border:1px solid #00d4e8;
                    padding:4px; font-family:Consolas; font-size:11px; }
            QMenu::item { padding:7px 22px; }
            QMenu::item:selected { background:#00d4e8; color:black; }
            QMenu::separator { background:#003040; height:1px; margin:3px 0; }
        """)
        menu.addAction("▶  Activate ULTRON",  self._start_ultron)
        menu.addAction("■  Deactivate",        self._stop_ultron)
        menu.addSeparator()
        menu.addAction("👁  Show",              self.show)
        menu.addAction("◻  Hide",              self.hide)
        menu.addSeparator()
        menu.addAction("🎮  Gaming Mode",       self._gaming_mode)
        menu.addAction("↺  Restart",           self._restart_ultron)
        menu.addAction("✕  Exit",              self._exit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _load_position(self):
        screen = QApplication.primaryScreen().geometry()
        try:
            with open(POS_FILE) as f:
                pos = json.load(f)
            x = max(0, min(pos.get('x', screen.width()-160),  screen.width()-140))
            y = max(0, min(pos.get('y', screen.height()-170), screen.height()-140))
            self.move(x, y)
        except:
            self.move(screen.width()-160, screen.height()-170)

    def _save_position(self):
        try:
            with open(POS_FILE, 'w') as f:
                json.dump({'x': self.x(), 'y': self.y()}, f)
        except: pass

    def _boot_tick(self):
        self.boot_alpha = min(self.boot_alpha + 0.025, 1.0)
        if self.boot_alpha >= 1.0:
            self.state = STATE_IDLE
            self.boot_timer.stop()

    def _tick(self):
        self.t           += 0.033
        self.ring_angle   = (self.ring_angle  + 1.2) % 360
        self.energy_angle = (self.energy_angle + 2.0) % 360
        self.wave_phase  += 0.15

        speed = {'idle':0.018,'hover':0.03,'listening':0.05,
                 'thinking':0.04,'speaking':0.06,'booting':0.02}.get(self.state,0.02)
        self.pulse += self.pulse_dir * speed
        if self.pulse >= 1.0: self.pulse_dir = -1
        if self.pulse <= 0.0: self.pulse_dir =  1

        for orb in self.orbitals:
            orb['angle'] += orb['speed']

        self.hover_scale += (self.target_scale - self.hover_scale) * 0.12

        target_glow = {'idle':0.4,'hover':0.8,'listening':0.9,
                       'thinking':0.7,'speaking':1.0,'booting':0.3}.get(self.state,0.5)
        self.glow_intensity += (target_glow - self.glow_intensity) * 0.08

        if self.state == STATE_SPEAKING:
            for i in range(len(self.speak_bars)):
                self.speak_bars[i] = abs(math.sin(self.wave_phase+i*0.7)) * random.uniform(0.5,1.0)
        else:
            for i in range(len(self.speak_bars)):
                self.speak_bars[i] *= 0.85

        self.update()

    def paintEvent(self, event):
        p   = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = 70, 70
        alpha  = min(self.boot_alpha, 1.0)
        sc     = self.hover_scale
        gi     = self.glow_intensity

        p.translate(cx, cy)
        p.scale(sc, sc)
        p.translate(-cx, -cy)

        # Outer rings
        pen = QPen(QColor(0,int(160*alpha),int(210*alpha),int(50*alpha)),1.2)
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        p.save(); p.translate(cx,cy); p.rotate(self.ring_angle*0.6)
        p.drawEllipse(QRectF(-66,-66,132,132)); p.restore()

        pen2 = QPen(QColor(0,int(200*alpha),int(230*alpha),int(35*alpha)),0.8)
        p.setPen(pen2)
        p.save(); p.translate(cx,cy); p.rotate(-self.ring_angle*1.1)
        p.drawEllipse(QRectF(-62,-62,124,124)); p.restore()

        if self.state == STATE_LISTENING:
            pen3 = QPen(QColor(0,int(100*alpha),int(200*alpha),int(120*alpha)),2)
            p.setPen(pen3)
            p.save(); p.translate(cx,cy); p.rotate(self.ring_angle*2)
            p.drawArc(QRectF(-58,-58,116,116),0,int(self.pulse*180*16)); p.restore()

        # Orbitals
        for orb in self.orbitals:
            ox = cx + orb['r']*math.cos(orb['angle'])
            oy = cy + orb['r']*math.sin(orb['angle'])
            bright = 0.5+0.5*math.sin(self.t*2+orb['phase'])
            a = int(160*bright*alpha)
            p.setBrush(QBrush(QColor(0,int(190*bright),int(230*bright),a)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(ox,oy),orb['size'],orb['size'])

        # Glow
        if self.is_running:
            gr = int(52+self.pulse*12)
            grad = QRadialGradient(QPointF(cx,cy),gr+18)
            grad.setColorAt(0,  QColor(0,200,230,int(70*gi*alpha)))
            grad.setColorAt(0.5,QColor(0,180,220,int(35*gi*alpha)))
            grad.setColorAt(1,  QColor(0,0,0,0))
            p.setBrush(QBrush(grad)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(cx,cy),gr+18,gr+18)

        # Body
        p.setBrush(QBrush(QColor(4,8,16,int(230*alpha))))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx,cy),52,52)

        # Energy border
        r,g,b = (0,180,220) if self.is_running else (0,60,80)
        for i in range(0,360,4):
            angle  = math.radians(i+self.energy_angle)
            bright = (math.sin(math.radians(i*2+self.t*70))+1)/2
            a      = int(200*bright*gi*alpha)
            p.setBrush(QBrush(QColor(int(r*bright),int(g*bright),int(b*bright),a)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(cx+52*math.cos(angle),cy+52*math.sin(angle)),2.2,2.2)

        # Face
        fc = QColor(0,int(210*alpha),int(230*alpha)) if self.is_running else QColor(0,int(80*alpha),int(100*alpha))
        p.setPen(QPen(fc,1.5)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(QRectF(cx-26,cy-33,52,52),18*16,144*16)
        p.drawLine(QPointF(cx-26,cy-12),QPointF(cx-20,cy+8))
        p.drawLine(QPointF(cx+26,cy-12),QPointF(cx+20,cy+8))
        p.drawLine(QPointF(cx-20,cy+8), QPointF(cx-7, cy+17))
        p.drawLine(QPointF(cx+20,cy+8), QPointF(cx+7, cy+17))
        p.drawLine(QPointF(cx-7, cy+17),QPointF(cx+7, cy+17))
        p.setPen(QPen(fc,2))
        p.drawLine(QPointF(cx-23,cy-11),QPointF(cx-10,cy-15))
        p.drawLine(QPointF(cx+23,cy-11),QPointF(cx+10,cy-15))

        # Eyes
        eye_lx,eye_rx,eye_y = cx-13,cx+13,cy-8
        if self.is_running:
            eg = int(70+self.pulse*130)
            for er in [11,8,5]:
                ea = int(eg*(1-er/13))
                p.setBrush(QBrush(QColor(0,220,240,ea)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(eye_lx,eye_y),er,er*0.55)
                p.drawEllipse(QPointF(eye_rx,eye_y),er,er*0.55)

        ec = QColor(0,int(230*alpha),int(255*alpha)) if self.is_running else QColor(0,int(60*alpha),int(80*alpha))
        p.setBrush(QBrush(ec)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(eye_lx,eye_y),6.5,3.8)
        p.drawEllipse(QPointF(eye_rx,eye_y),6.5,3.8)
        p.setBrush(QBrush(QColor(200,255,255,int(230*alpha))))
        p.drawEllipse(QPointF(eye_lx,eye_y),2.8,1.8)
        p.drawEllipse(QPointF(eye_rx,eye_y),2.8,1.8)

        # Mouth
        p.setPen(QPen(fc,1.5))
        my  = cy+10
        pts = [QPointF(cx-11,my),QPointF(cx-6,my+4),QPointF(cx-2,my+1),
               QPointF(cx,my+5),QPointF(cx+2,my+1),QPointF(cx+6,my+4),QPointF(cx+11,my)]
        for i in range(len(pts)-1): p.drawLine(pts[i],pts[i+1])

        # Status label
        p.setPen(QColor(0,int(200*alpha),int(220*alpha),int(160*alpha)))
        p.setFont(QFont("Consolas",5,QFont.Weight.Bold))
        labels = {STATE_IDLE:"STANDBY",STATE_HOVER:"READY",
                  STATE_LISTENING:"LISTENING",STATE_THINKING:"THINKING",
                  STATE_SPEAKING:"SPEAKING",STATE_BOOTING:"BOOTING"}
        label = labels.get(self.state,"ULTRON")
        if self.is_running and self.state == STATE_IDLE: label = "ONLINE"
        p.drawText(QRectF(cx-30,cy+24,60,12),Qt.AlignmentFlag.AlignCenter,label)

        # Speaking bars
        if self.state == STATE_SPEAKING:
            bw=5; total=8*(bw+2); sx=cx-total//2
            for i,h in enumerate(self.speak_bars):
                bh=max(3,int(h*22)); bx=sx+i*(bw+2); by=cy+32-bh//2
                a=int(200*alpha*(0.4+h*0.6))
                p.setBrush(QBrush(QColor(0,220,180,a)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(QRectF(bx,by,bw,bh),2,2)

        # Listening ripples
        if self.state == STATE_LISTENING:
            for i in range(1,4):
                progress=(self.t*0.8+i*0.3)%1.0
                ring_r=52+progress*25
                a=int(120*(1-progress)*alpha)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor(0,140,255,a),1.5))
                p.drawEllipse(QPointF(cx,cy),ring_r,ring_r)

        # Status dot
        dot = QColor(0,220,80) if self.is_running else QColor(50,50,70)
        if self.state == STATE_LISTENING: dot = QColor(0,140,255)
        if self.state == STATE_THINKING:  dot = QColor(130,60,220)
        p.setBrush(QBrush(dot)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx+40,cy-40),6,6)
        if self.is_running:
            pr=6+self.pulse*4
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(0,220,80,int(80*(1-self.pulse))),1))
            p.drawEllipse(QPointF(cx+40,cy-40),pr,pr)

        p.end()

    def enterEvent(self, event):
        self.state=STATE_HOVER; self.target_scale=1.08

    def leaveEvent(self, event):
        if self.state==STATE_HOVER: self.state=STATE_IDLE
        self.target_scale=1.0

    def mousePressEvent(self, event):
        if event.button()==Qt.MouseButton.LeftButton:
            self.drag_pos=event.globalPosition().toPoint()-self.frameGeometry().topLeft()
            self.is_dragging=False
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons()==Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint()-self.drag_pos)
            self.is_dragging=True
            self._save_position()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button()==Qt.MouseButton.LeftButton and not self.is_dragging:
            self._on_click()
        self.is_dragging=False

    def mouseDoubleClickEvent(self, event):
        if event.button()==Qt.MouseButton.LeftButton:
            if self.is_running: self._stop_ultron()
            else:               self._start_ultron()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background:#000d0f; color:#00d4e8; border:1px solid #00d4e8;
                    padding:4px; font-family:Consolas; font-size:11px; }
            QMenu::item { padding:7px 22px; }
            QMenu::item:selected { background:#00d4e8; color:black; }
            QMenu::separator { background:#003040; height:1px; margin:3px 0; }
        """)
        menu.addAction("▶  Activate ULTRON",   self._start_ultron)
        menu.addAction("■  Deactivate ULTRON",  self._stop_ultron)
        menu.addSeparator()
        menu.addAction("🎮  Gaming Mode",        self._gaming_mode)
        menu.addAction("💻  VS Code",            self._coding_mode)
        menu.addSeparator()
        menu.addAction("↺  Restart ULTRON",     self._restart_ultron)
        menu.addAction("✕  Exit",               self._exit)
        menu.exec(event.globalPos())

    def _on_click(self):
        if not self.is_running:
            self._start_ultron()
            return
        # Send wake signal to running ultron.py
        try:
            with open(SIGNAL_FILE,'w') as f: f.write("WAKE")
            self.state = STATE_LISTENING
            print("[WIDGET] Wake signal sent")
        except Exception as e:
            print(f"[WIDGET] Signal error: {e}")

    def _start_ultron(self):
        if self.is_running: return
        self.ultron_proc = subprocess.Popen(
            [PYTHON, ULTRON_PATH],
            cwd           = BASE_DIR,
            creationflags = subprocess.CREATE_NEW_CONSOLE
        )
        self.is_running = True
        self.state      = STATE_IDLE
        threading.Thread(target=self._monitor, daemon=True).start()

    def _stop_ultron(self):
        if self.ultron_proc:
            try: self.ultron_proc.terminate()
            except: pass
            self.ultron_proc = None
        self.is_running = False
        self.state      = STATE_IDLE

    def _restart_ultron(self):
        self._stop_ultron()
        time.sleep(1)
        self._start_ultron()

    def _gaming_mode(self):
        try:
            from gaming_mode.gaming_mode import start_gaming_mode
            start_gaming_mode("asphalt")
        except Exception as e:
            print(f"[WIDGET] Gaming error: {e}")

    def _coding_mode(self):
        try:
            from executor.app_launcher import launch_app
            launch_app("vs code")
        except: pass

    def _monitor(self):
        if self.ultron_proc:
            self.ultron_proc.wait()
            self.is_running = False
            self.state      = STATE_IDLE

    def _tray_activated(self, reason):
        if reason==QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible(): self.hide()
            else:                self.show()

    def _exit(self):
        self._stop_ultron()
        self._save_position()
        QApplication.quit()

    def set_state(self, state: str):
        if state in [STATE_IDLE,STATE_LISTENING,STATE_THINKING,STATE_SPEAKING]:
            self.state = state

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("ULTRON OS")
    w   = UltronCompanion()
    sys.exit(app.exec())