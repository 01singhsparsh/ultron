"""
app_launcher_hud.py
Holographic floating app launcher.
Appears after ULTRON greeting. Click or voice to open apps.
Expanding animation when app opens.
"""
import sys, os, math, time, threading
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore    import Qt, QTimer, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui     import (QPainter, QColor, QPen, QBrush, QFont,
                              QRadialGradient, QLinearGradient)

APPS = [
    {"name":"Brave",    "color":QColor(255,100,50),  "action":"app",     "target":"brave",                  "letter":"B"},
    {"name":"WhatsApp", "color":QColor(37,211,102),  "action":"app",     "target":"whatsapp",               "letter":"W"},
    {"name":"ChatGPT",  "color":QColor(16,163,127),  "action":"website", "target":"https://chatgpt.com",    "letter":"G"},
    {"name":"Claude",   "color":QColor(210,120,50),  "action":"website", "target":"https://claude.ai",      "letter":"C"},
    {"name":"YouTube",  "color":QColor(255,0,0),     "action":"website", "target":"https://youtube.com",    "letter":"Y"},
    {"name":"VS Code",  "color":QColor(0,120,215),   "action":"app",     "target":"code",                   "letter":"V"},
]

class AppLauncherHUD(QWidget):
    def __init__(self):
        super().__init__()
        screen   = QApplication.primaryScreen().geometry()
        self.SW  = screen.width()
        self.SH  = screen.height()
        self.cx  = self.SW // 2
        self.cy  = self.SH // 2

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(0, 0, self.SW, self.SH)
        self.setMouseTracking(True)

        self.t             = 0.0
        self.active        = False
        self.bg_alpha      = 0.0
        self.icons         = []
        self.hover_idx     = -1
        self.launching     = False
        self.launch_scale  = 0.0
        self.launch_color  = QColor(0,210,230)
        self.launch_name   = ""
        self.launch_x      = float(self.cx)
        self.launch_y      = float(self.cy)
        self.question_alpha= 0.0
        self.closing       = False
        self.close_alpha   = 1.0

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def show_launcher(self):
        self.icons = []
        total      = len(APPS)
        for i, app in enumerate(APPS):
            angle   = (2*math.pi/total)*i - math.pi/2
            radius  = 230
            icon    = {
                "app":      app,
                "tx":       self.cx + radius*math.cos(angle),
                "ty":       self.cy + radius*math.sin(angle),
                "x":        float(self.cx),
                "y":        float(self.cy),
                "alpha":    0.0,
                "scale":    0.0,
                "pulse":    0.0,
                "pulse_dir":1,
                "hover":    False,
                "launched": False,
                "draw_y":   float(self.cy),
            }
            self.icons.append(icon)

        self.active        = True
        self.bg_alpha      = 0.0
        self.question_alpha= 0.0
        self.launching     = False
        self.closing       = False
        self.close_alpha   = 1.0
        self.t             = 0.0
        self.show()
        self.raise_()
        self.activateWindow()
        print("[LAUNCHER] Shown")

    def hide_launcher(self):
        self.closing = True

    def _tick(self):
        if not self.active: return
        self.t += 0.033

        if not self.closing:
            self.bg_alpha = min(0.75, self.bg_alpha+0.025)

        # Update icons
        for i, icon in enumerate(self.icons):
            delay = i * 0.12
            if self.t > delay:
                icon["alpha"] = min(1.0, icon["alpha"]+0.05)
                icon["scale"] = min(1.0, icon["scale"]+0.05)
                icon["x"]    += (icon["tx"]-icon["x"])*0.18
                icon["y"]    += (icon["ty"]-icon["y"])*0.18
            icon["draw_y"] = icon["y"] + math.sin(self.t*1.5+i*1.0)*7
            icon["pulse"] += icon["pulse_dir"]*0.03
            if icon["pulse"] >= 1.0: icon["pulse_dir"] = -1
            if icon["pulse"] <= 0.0: icon["pulse_dir"] =  1

        if self.t > 1.8:
            self.question_alpha = min(1.0, self.question_alpha+0.04)

        # Launch animation
        if self.launching:
            self.launch_scale += 0.055
            if self.launch_scale >= 1.0:
                self.launching = False
                self.active    = False
                self.hide()
                return

        # Close animation
        if self.closing:
            self.close_alpha = max(0.0, self.close_alpha-0.06)
            if self.close_alpha <= 0:
                self.active = False
                self.hide()
                return

        self.update()

    def _do_launch(self, icon: dict):
        """Trigger expanding launch animation then open app."""
        if icon["launched"]: return
        icon["launched"]   = True
        self.launching     = True
        self.launch_scale  = 0.03
        self.launch_color  = icon["app"]["color"]
        self.launch_name   = icon["app"]["name"]
        self.launch_x      = icon["x"]
        self.launch_y      = icon["draw_y"]

        def _open():
            time.sleep(0.7)
            app = icon["app"]
            try:
                if app["action"] == "app":
                    from executor.app_launcher import launch_app
                    launch_app(app["target"])
                else:
                    import webbrowser
                    webbrowser.open(app["target"])
            except Exception as e:
                print(f"[LAUNCHER] Open error: {e}")

        threading.Thread(target=_open, daemon=True).start()

    def paintEvent(self, event):
        if not self.active: return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        am = self.close_alpha

        # Dark overlay
        p.fillRect(0,0,self.SW,self.SH,
                  QColor(0,5,12,int(170*self.bg_alpha*am)))

        # Grid
        a = int(18*am)
        p.setPen(QPen(QColor(0,210,230,a),1))
        for x in range(0,self.SW,80): p.drawLine(x,0,x,self.SH)
        for y in range(0,self.SH,80): p.drawLine(0,y,self.SW,y)

        # Launch animation (covers screen)
        if self.launching:
            self._draw_launch(p)
            p.end()
            return

        # Connection lines
        for icon in self.icons:
            if icon["alpha"] < 0.2: continue
            a = int(35*icon["alpha"]*am)
            col = icon["app"]["color"]
            p.setPen(QPen(QColor(col.red(),col.green(),col.blue(),a),1))
            p.drawLine(QPointF(self.cx,self.cy),
                      QPointF(icon["x"],icon["draw_y"]))

        # Center hub
        self._draw_center(p, am)

        # Icons
        for icon in self.icons:
            if icon["alpha"] > 0:
                self._draw_icon(p, icon, am)

        # Question text
        if self.question_alpha > 0:
            self._draw_question(p, am)

        p.end()

    def _draw_center(self, p, am):
        cx,cy = self.cx,self.cy
        pulse = 0.7+0.3*math.sin(self.t*3)
        # Glow
        g = QRadialGradient(QPointF(cx,cy),85)
        g.setColorAt(0,  QColor(0,210,230,int(55*am)))
        g.setColorAt(0.5,QColor(0,150,180,int(25*am)))
        g.setColorAt(1,  QColor(0,0,0,0))
        p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx,cy),85,85)
        # Rings
        for r in [48,36,24]:
            a = int(100*pulse*am)
            p.setPen(QPen(QColor(0,210,230,a),1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx,cy),r,r)
        # Text
        p.setFont(QFont("Consolas",12,QFont.Weight.Bold))
        p.setPen(QPen(QColor(0,210,230,int(220*am)),1))
        p.drawText(QRectF(cx-45,cy-13,90,26),Qt.AlignmentFlag.AlignCenter,"ULTRON")

    def _draw_icon(self, p, icon, am):
        x   = int(icon["x"]); y = int(icon["draw_y"])
        s   = int(68*icon["scale"]); a = icon["alpha"]*am
        col = icon["app"]["color"]
        pulse = 0.85+0.15*math.sin(self.t*2+self.icons.index(icon))

        # Hover glow
        if icon["hover"]:
            g = QRadialGradient(QPointF(x,y),s+25)
            g.setColorAt(0,QColor(col.red(),col.green(),col.blue(),int(90*a)))
            g.setColorAt(1,QColor(0,0,0,0))
            p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(x,y),s+25,s+25)

        # Outer ring
        p.setPen(QPen(QColor(col.red(),col.green(),col.blue(),int(160*a*pulse)),2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(x,y),s//2+10,s//2+10)

        # Background circle
        bg = QRadialGradient(QPointF(x-s//5,y-s//5),s)
        bg.setColorAt(0,QColor(min(255,col.red()+60),min(255,col.green()+60),
                              min(255,col.blue()+60),int(230*a)))
        bg.setColorAt(1,QColor(col.red()//2,col.green()//2,col.blue()//2,int(210*a)))
        p.setBrush(QBrush(bg))
        p.setPen(QPen(QColor(col.red(),col.green(),col.blue(),int(200*a)),2))
        p.drawEllipse(QPointF(x,y),s//2,s//2)

        # Letter
        p.setFont(QFont("Consolas",int(s*0.32),QFont.Weight.Bold))
        p.setPen(QPen(QColor(255,255,255,int(245*a)),1))
        p.drawText(QRectF(x-s//2,y-s//2,s,s),Qt.AlignmentFlag.AlignCenter,icon["app"]["letter"])

        # Name below
        p.setFont(QFont("Consolas",9))
        p.setPen(QPen(QColor(255,255,255,int(200*a)),1))
        p.drawText(QRectF(x-55,y+s//2+8,110,20),Qt.AlignmentFlag.AlignCenter,icon["app"]["name"])

        # Pulse ring
        pr = s//2+10+icon["pulse"]*14
        pa = int(80*a*(1-icon["pulse"]))
        p.setPen(QPen(QColor(col.red(),col.green(),col.blue(),pa),1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(x,y),pr,pr)

    def _draw_question(self, p, am):
        a  = self.question_alpha*am
        cy = self.SH-110
        p.setBrush(QBrush(QColor(0,8,16,int(190*a))))
        p.setPen(QPen(QColor(0,210,230,int(110*a)),1))
        p.drawRect(self.cx-320,cy-22,640,52)
        p.setPen(QPen(QColor(0,210,230,int(200*a)),1))
        p.drawLine(self.cx-320,cy-22,self.cx+320,cy-22)
        p.setFont(QFont("Consolas",14,QFont.Weight.Bold))
        p.setPen(QPen(QColor(0,210,230,int(235*a)),1))
        p.drawText(QRectF(self.cx-320,cy-17,640,36),
                  Qt.AlignmentFlag.AlignCenter,"What are we working on today Sir?")
        p.setFont(QFont("Consolas",8))
        p.setPen(QPen(QColor(0,210,230,int(130*a)),1))
        p.drawText(QRectF(self.cx-320,cy+33,640,20),
                  Qt.AlignmentFlag.AlignCenter,
                  "Click an icon  |  Say the app name  |  ESC to dismiss")

    def _draw_launch(self, p):
        """Expanding color fills the screen — app name in center."""
        s     = self.launch_scale
        col   = self.launch_color
        max_r = math.sqrt(self.SW**2+self.SH**2)
        r     = s * max_r

        g = QRadialGradient(QPointF(self.launch_x,self.launch_y),r)
        g.setColorAt(0,  QColor(col.red()//2,col.green()//2,col.blue()//2,255))
        g.setColorAt(0.4,QColor(col.red(),col.green(),col.blue(),230))
        g.setColorAt(0.8,QColor(col.red()//3,col.green()//3,col.blue()//3,180))
        g.setColorAt(1,  QColor(0,0,0,0))
        p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(self.launch_x,self.launch_y),r,r)

        # Ripple rings
        for i in range(3):
            rr = r-i*50
            if rr > 0:
                a = int(160*(1-i/3)*(1-s))
                p.setPen(QPen(QColor(255,255,255,a),2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(self.launch_x,self.launch_y),rr,rr)

        # App name
        a = int(255*(1-s))
        p.setFont(QFont("Consolas",42,QFont.Weight.Bold))
        p.setPen(QPen(QColor(255,255,255,a),1))
        p.drawText(QRectF(0,0,self.SW,self.SH),
                  Qt.AlignmentFlag.AlignCenter, self.launch_name)

    def mouseMoveEvent(self, event):
        px,py = event.position().x(), event.position().y()
        for i,icon in enumerate(self.icons):
            dx = px - icon["x"]; dy = py - icon["draw_y"]
            icon["hover"] = math.sqrt(dx*dx+dy*dy) < 44
        self.update()

    def mousePressEvent(self, event):
        if event.button()==Qt.MouseButton.LeftButton:
            px,py = event.position().x(), event.position().y()
            for icon in self.icons:
                dx=px-icon["x"]; dy=py-icon["draw_y"]
                if math.sqrt(dx*dx+dy*dy) < 44 and not icon["launched"]:
                    self._do_launch(icon)
                    return
        if event.button()==Qt.MouseButton.RightButton:
            self.hide_launcher()

    def keyPressEvent(self, event):
        if event.key()==Qt.Key.Key_Escape:
            self.hide_launcher()

    def voice_select(self, text: str) -> bool:
        text_lower = text.lower()
        for icon in self.icons:
            name = icon["app"]["name"].lower()
            if name in text_lower or text_lower in name:
                self._do_launch(icon)
                return True
        return False


# ── Global instance ──
_launcher = None

def init_launcher(app) -> AppLauncherHUD:
    global _launcher
    _launcher = AppLauncherHUD()
    return _launcher

def get_launcher() -> AppLauncherHUD:
    return _launcher

def show_launcher():
    if _launcher: _launcher.show_launcher()

def hide_launcher():
    if _launcher: _launcher.hide_launcher()

def voice_launch(text: str) -> bool:
    if _launcher and _launcher.active:
        return _launcher.voice_select(text)
    return False