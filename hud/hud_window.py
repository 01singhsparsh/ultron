"""
hud_window.py
Iron Man AR Desktop Overlay.
Reads state from shared JSON file — works across processes.
Low CPU. Desktop level. Click-through.
"""
import sys, os, math, time, psutil, json
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUD_FILE = os.path.join(BASE_DIR, "data", "hud_state.json")

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore    import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui     import (QPainter, QColor, QPen, QBrush, QFont,
                              QLinearGradient, QRadialGradient)
import ctypes

GWL_EXSTYLE       = -20
WS_EX_LAYERED     = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
HWND_BOTTOM       = 1
SWP_NOMOVE        = 0x0002
SWP_NOSIZE        = 0x0001
SWP_NOACTIVATE    = 0x0010
SWP_SHOWWINDOW    = 0x0040

class IronManHUD(QWidget):
    def __init__(self):
        super().__init__()
        screen  = QApplication.primaryScreen().geometry()
        self.SW = screen.width()
        self.SH = screen.height()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setGeometry(0, 0, self.SW, self.SH)

        # Animation
        self.t             = 0.0
        self.scan_y        = 0
        self.scan_dir      = 1
        self.pulse         = 0.0
        self.pulse_dir     = 1
        self.ring_angle    = 0.0
        self.energy_angle  = 0.0
        self.boot_progress = 0.0
        self.booting       = True
        self.notifications = []
        self.speak_bars    = [0.0] * 12
        self.wave_phase    = 0.0

        # System
        self.cpu     = 0
        self.ram     = 0
        self.battery = 0
        self.plugged = False

        # State
        self.ultron_state   = "ONLINE"
        self.last_command   = ""
        self.heard_text     = ""
        self.heard_alpha    = 0.0
        self.response_text  = ""
        self.response_alpha = 0.0

        # Colors
        self.CYAN   = QColor(0,   210, 230)
        self.GREEN  = QColor(50,  230, 80)
        self.ORANGE = QColor(255, 160, 30)
        self.DIM    = QColor(0,   80,  100)

        # Timers — low CPU
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._tick)
        self.anim_timer.start(66)  # 15 FPS

        self.sys_timer = QTimer()
        self.sys_timer.timeout.connect(self._update_system)
        self.sys_timer.start(8000)

        self.pos_timer = QTimer()
        self.pos_timer.timeout.connect(self._send_to_desktop)
        self.pos_timer.start(15000)

        self._update_system()
        self.show()
        QTimer.singleShot(400, self._apply_win32)

    def _apply_win32(self):
        try:
            hwnd  = int(self.winId())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE,
                style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            )
            self._send_to_desktop()
        except Exception as e:
            print(f"[HUD] Win32 error: {e}")

    def _send_to_desktop(self):
        try:
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowPos(
                hwnd, HWND_BOTTOM, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
            )
        except: pass

    def _read_hud_file(self):
        """Read shared state file written by ultron.py."""
        try:
            if not os.path.exists(HUD_FILE): return
            with open(HUD_FILE, 'r') as f:
                data = json.load(f)
            if not data: return

            if data.get("heard"):
                self.heard_text  = data["heard"][:55]
                self.heard_alpha = 1.0

            if data.get("response"):
                self.response_text  = data["response"][:80]
                self.response_alpha = 1.0

            if data.get("state"):
                self.ultron_state = data["state"].upper()

            # Clear file after reading
            with open(HUD_FILE, 'w') as f:
                json.dump({}, f)
        except: pass

    def _tick(self):
        # Read shared state from ultron.py process
        self._read_hud_file()

        self.t            += 0.1
        self.ring_angle    = (self.ring_angle   + 2.5) % 360
        self.energy_angle  = (self.energy_angle + 4.0) % 360

        self.pulse += self.pulse_dir * 0.05
        if self.pulse >= 1.0: self.pulse_dir = -1
        if self.pulse <= 0.0: self.pulse_dir =  1

        self.scan_y += self.scan_dir * 5
        if self.scan_y > self.SH: self.scan_dir = -1
        if self.scan_y < 0:       self.scan_dir =  1

        if self.booting:
            self.boot_progress = min(self.boot_progress + 0.015, 1.0)
            if self.boot_progress >= 1.0: self.booting = False

        self.wave_phase += 0.3
        if self.ultron_state == "SPEAKING":
            import random
            for i in range(len(self.speak_bars)):
                self.speak_bars[i] = abs(math.sin(self.wave_phase+i*0.6)) * random.uniform(0.4,1.0)
        else:
            for i in range(len(self.speak_bars)):
                self.speak_bars[i] *= 0.85

        # Fade heard/response text slowly
        if self.heard_alpha    > 0: self.heard_alpha    = max(0, self.heard_alpha    - 0.015)
        if self.response_alpha > 0: self.response_alpha = max(0, self.response_alpha - 0.008)

        for n in self.notifications:
            n['alpha'] = max(0, n['alpha'] - 0.008)
        self.notifications = [n for n in self.notifications if n['alpha'] > 0]

        self.update()

    def _update_system(self):
        try:
            self.cpu = int(psutil.cpu_percent(interval=0))
            self.ram = int(psutil.virtual_memory().percent)
            b = psutil.sensors_battery()
            if b: self.battery = int(b.percent); self.plugged = b.power_plugged
        except: pass

    def set_state(self, state):  self.ultron_state = state.upper()
    def set_command(self, cmd):  self.last_command = cmd[:50]
    def set_heard(self, text):   self.heard_text   = text[:55]; self.heard_alpha    = 1.0
    def set_response(self, text):self.response_text = text[:80]; self.response_alpha = 1.0
    def add_notification(self, text): self.notifications.append({'text':text[:38],'alpha':1.0})

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        alpha = min(self.boot_progress, 1.0)
        self._draw_scan_line(p, alpha)
        self._draw_corner_brackets(p, alpha)
        self._draw_top_left_clock(p, alpha)
        self._draw_top_right_stats(p, alpha)
        self._draw_bottom_left_status(p, alpha)
        self._draw_bottom_right_arc(p, alpha)
        self._draw_center(p, alpha)
        self._draw_waveform(p, alpha)
        self._draw_notifications(p)
        self._draw_horizon(p, alpha)
        p.end()

    def _panel(self, p, x, y, w, h, alpha):
        p.setBrush(QBrush(QColor(0,8,16,int(140*alpha))))
        p.setPen(QPen(QColor(0,210,230,int(60*alpha)),1))
        p.drawRect(int(x),int(y),int(w),int(h))
        p.setPen(QPen(QColor(0,210,230,int(120*alpha)),1))
        p.drawLine(int(x),int(y),int(x+w),int(y))

    def _mini_bar(self, p, x, y, w, h, value, color, alpha):
        p.setBrush(QBrush(QColor(0,40,50,int(120*alpha))))
        p.setPen(QPen(QColor(0,100,120,int(80*alpha)),1))
        p.drawRect(int(x),int(y),int(w),int(h))
        fill = int(w*max(0,min(1,value)))
        if fill > 0:
            g = QLinearGradient(x,y,x+w,y)
            g.setColorAt(0,QColor(color.red()//2,color.green()//2,color.blue()//2,int(180*alpha)))
            g.setColorAt(1,QColor(color.red(),color.green(),color.blue(),int(200*alpha)))
            p.fillRect(int(x)+1,int(y)+1,fill-1,int(h)-1,QBrush(g))

    def _draw_scan_line(self, p, alpha):
        if alpha < 0.5: return
        g = QLinearGradient(0,self.scan_y-20,0,self.scan_y+20)
        g.setColorAt(0,QColor(0,210,230,0))
        g.setColorAt(0.5,QColor(0,210,230,int(5*alpha)))
        g.setColorAt(1,QColor(0,210,230,0))
        p.fillRect(0,self.scan_y-20,self.SW,40,QBrush(g))

    def _draw_corner_brackets(self, p, alpha):
        size=55; a=int(160*alpha)
        pen=QPen(QColor(0,210,230,a),2)
        corners=[(0,0,1,1),(self.SW,0,-1,1),(0,self.SH,1,-1),(self.SW,self.SH,-1,-1)]
        p.setPen(pen)
        for cx,cy,dx,dy in corners:
            p.drawLine(int(cx),int(cy),int(cx+dx*size),int(cy))
            p.drawLine(int(cx),int(cy),int(cx),int(cy+dy*size))
            p.setPen(QPen(QColor(0,210,230,int(a*0.35)),1))
            p.drawLine(int(cx+dx*8),int(cy+dy*8),int(cx+dx*(size-8)),int(cy+dy*8))
            p.drawLine(int(cx+dx*8),int(cy+dy*8),int(cx+dx*8),int(cy+dy*(size-8)))
            p.setPen(pen)

    def _draw_top_left_clock(self, p, alpha):
        import datetime
        now=datetime.datetime.now(); x,y=80,80
        self._panel(p,x-10,y-10,280,158,alpha*0.6)
        p.setFont(QFont("Consolas",30,QFont.Weight.Bold))
        p.setPen(QPen(QColor(0,210,230,int(220*alpha)),1))
        p.drawText(x,y+35,now.strftime("%H:%M:%S"))
        p.setFont(QFont("Consolas",9))
        p.setPen(QPen(QColor(0,210,230,int(150*alpha)),1))
        p.drawText(x,y+55,now.strftime("%A  %d %B %Y"))
        p.setPen(QPen(QColor(0,210,230,int(70*alpha)),1))
        p.drawLine(x,y+64,x+260,y+64)
        p.setFont(QFont("Consolas",8))
        p.setPen(QPen(QColor(0,210,230,int(110*alpha)),1))
        p.drawText(x,y+80,f"CPU   {self.cpu:3d}%")
        p.drawText(x,y+94,f"RAM   {self.ram:3d}%")
        p.drawText(x,y+108,f"BATT  {self.battery:3d}%  {'CHARGING' if self.plugged else 'ON BATTERY'}")
        self._mini_bar(p,x+115,y+70,145,10,self.cpu/100,   self.GREEN, alpha)
        self._mini_bar(p,x+115,y+84,145,10,self.ram/100,   self.ORANGE,alpha)
        self._mini_bar(p,x+115,y+98,145,10,self.battery/100,self.CYAN, alpha)

    def _draw_top_right_stats(self, p, alpha):
        x=self.SW-290; y=80
        self._panel(p,x-10,y-10,280,125,alpha*0.6)
        p.setFont(QFont("Consolas",9,QFont.Weight.Bold))
        p.setPen(QPen(QColor(0,210,230,int(190*alpha)),1))
        p.drawText(x,y+15,"SYSTEM MONITOR")
        p.setPen(QPen(QColor(0,210,230,int(70*alpha)),1))
        p.drawLine(x,y+21,x+260,y+21)
        items=[
            ("ULTRON",  self.ultron_state,
             self.GREEN if self.ultron_state in ["ONLINE","SPEAKING"] else self.ORANGE),
            ("MEMORY",  "ACTIVE",    self.GREEN),
            ("VISION",  "STANDBY",   self.DIM),
            ("SESSION", "RECORDING", self.GREEN),
        ]
        p.setFont(QFont("Consolas",8))
        for i,(label,status,col) in enumerate(items):
            iy=y+37+i*20
            p.setPen(QPen(QColor(0,210,230,int(140*alpha)),1))
            p.drawText(x,iy,label)
            p.setBrush(QBrush(QColor(col.red(),col.green(),col.blue(),int(210*alpha))))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(x+90),int(iy-8),8,8)
            p.setPen(QPen(QColor(col.red(),col.green(),col.blue(),int(170*alpha)),1))
            p.drawText(x+106,iy,status)

    def _draw_bottom_left_status(self, p, alpha):
        x=80; y=self.SH-285
        self._panel(p,x-10,y-10,320,215,alpha*0.6)

        p.setFont(QFont("Consolas",11,QFont.Weight.Bold))
        p.setPen(QPen(QColor(0,210,230,int(210*alpha)),1))
        p.drawText(x,y+15,"ULTRON OS")
        p.setPen(QPen(QColor(0,210,230,int(60*alpha)),1))
        p.drawLine(x,y+21,x+300,y+21)

        col={
            "ONLINE":   self.GREEN,
            "LISTENING":self.CYAN,
            "THINKING": self.ORANGE,
            "SPEAKING": QColor(0,230,180),
        }.get(self.ultron_state, self.DIM)

        pr=int(6+self.pulse*3)
        p.setBrush(QBrush(QColor(col.red(),col.green(),col.blue(),int(170*alpha))))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(x),int(y+30),pr*2,pr*2)
        p.setFont(QFont("Consolas",10,QFont.Weight.Bold))
        p.setPen(QPen(QColor(col.red(),col.green(),col.blue(),int(210*alpha)),1))
        p.drawText(x+22,y+44,self.ultron_state)

        # Divider
        p.setPen(QPen(QColor(0,210,230,int(40*alpha)),1))
        p.drawLine(x,y+56,x+300,y+56)

        # What ULTRON heard — blue
        if self.heard_alpha > 0:
            a = self.heard_alpha * alpha
            p.setFont(QFont("Consolas",8,QFont.Weight.Bold))
            p.setPen(QPen(QColor(0,140,255,int(220*a)),1))
            p.drawText(x,y+74,self.heard_text[:38])

        # ULTRON response — green
        if self.response_alpha > 0:
            a = self.response_alpha * alpha
            p.setFont(QFont("Consolas",8))
            p.setPen(QPen(QColor(0,230,180,int(200*a)),1))
            txt = self.response_text
            p.drawText(x,y+92, f"◄ {txt[:36]}")
            if len(txt) > 36:
                p.drawText(x,y+106,f"  {txt[36:72]}")
            if len(txt) > 72:
                p.drawText(x,y+120,f"  {txt[72:108]}")

        # Uptime
        p.setFont(QFont("Consolas",7))
        p.setPen(QPen(QColor(0,210,230,int(75*alpha)),1))
        uptime=int(time.time())%3600
        p.drawText(x,y+142,f"UPTIME  {uptime//60:02d}:{uptime%60:02d}")
        p.drawText(x,y+155,"POWERED BY GROQ + LLAMA 3.3 70B")

    def _draw_bottom_right_arc(self, p, alpha):
        cx=self.SW-130; cy=self.SH-130; r=75
        for i in range(0,360,10):
            angle=math.radians(i+self.ring_angle)
            bright=(math.sin(math.radians(i*3+self.t*50))+1)/2
            a=int(140*bright*alpha)
            px=cx+r*math.cos(angle); py=cy+r*math.sin(angle)
            p.setBrush(QBrush(QColor(0,int(180*bright),int(230*bright),a)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(px,py),2.5,2.5)
        pen=QPen(QColor(0,210,230,int(110*alpha)),1.5)
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        p.save(); p.translate(cx,cy); p.rotate(-self.ring_angle*1.5)
        p.drawEllipse(QRectF(-r+14,-r+14,(r-14)*2,(r-14)*2)); p.restore()
        p.setPen(QPen(QColor(0,210,230,int(80*alpha)),1))
        p.save(); p.translate(cx,cy); p.rotate(self.energy_angle)
        p.drawEllipse(QRectF(-r+28,-r+28,(r-28)*2,(r-28)*2)); p.restore()
        cr=int(18+self.pulse*7)
        g=QRadialGradient(QPointF(cx,cy),cr+10)
        g.setColorAt(0,  QColor(0,230,255,int(170*alpha)))
        g.setColorAt(0.5,QColor(0,180,220,int(90*alpha)))
        g.setColorAt(1,  QColor(0,0,0,0))
        p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx,cy),cr+10,cr+10)
        p.setBrush(QBrush(QColor(0,230,255,int(210*alpha))))
        p.drawEllipse(QPointF(cx,cy),cr,cr)
        p.setBrush(QBrush(QColor(200,255,255,int(230*alpha))))
        p.drawEllipse(QPointF(cx,cy),7,7)
        for i in range(6):
            angle=math.radians(self.energy_angle+i*60)
            x1=cx+11*math.cos(angle); y1=cy+11*math.sin(angle)
            x2=cx+(r-16)*math.cos(angle); y2=cy+(r-16)*math.sin(angle)
            p.setPen(QPen(QColor(0,210,230,int(90*alpha)),1.5))
            p.drawLine(QPointF(x1,y1),QPointF(x2,y2))
        p.setFont(QFont("Consolas",7,QFont.Weight.Bold))
        p.setPen(QPen(QColor(0,210,230,int(110*alpha)),1))
        p.drawText(int(cx-35),int(cy+r+16),"ARC REACTOR")

    def _draw_center(self, p, alpha):
        cx=self.SW//2; cy=self.SH//2
        if self.booting:
            r=110; prog=self.boot_progress
            p.setPen(QPen(QColor(0,210,230,int(190*alpha)),3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRectF(cx-r,cy-r,r*2,r*2),90*16,-int(prog*360*16))
            p.setFont(QFont("Consolas",22,QFont.Weight.Bold))
            p.setPen(QPen(QColor(0,210,230,int(210*alpha)),1))
            p.drawText(QRectF(cx-50,cy-16,100,32),Qt.AlignmentFlag.AlignCenter,f"{int(prog*100)}%")
            p.setFont(QFont("Consolas",8))
            p.setPen(QPen(QColor(0,210,230,int(140*alpha)),1))
            p.drawText(QRectF(cx-80,cy+22,160,18),Qt.AlignmentFlag.AlignCenter,"INITIALIZING ULTRON OS")
            msgs=["LOADING MEMORY...","INIT VOICE...","ACTIVATING AI CORE...","ULTRON OS READY"]
            shown=int(prog*len(msgs))
            p.setFont(QFont("Consolas",7))
            p.setPen(QPen(QColor(0,210,230,int(90*alpha)),1))
            for i in range(min(shown+1,len(msgs))):
                p.drawText(QRectF(cx-90,cy+46+i*14,180,14),Qt.AlignmentFlag.AlignCenter,f"> {msgs[i]}")
            return
        s=25; a=int(25*alpha)
        p.setPen(QPen(QColor(0,210,230,a),1))
        p.drawLine(cx-s,cy,cx-6,cy); p.drawLine(cx+6,cy,cx+s,cy)
        p.drawLine(cx,cy-s,cx,cy-6); p.drawLine(cx,cy+6,cx,cy+s)
        p.setBrush(QBrush(QColor(0,210,230,a))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx,cy),2.5,2.5)

    def _draw_waveform(self, p, alpha):
        if max(self.speak_bars) < 0.05: return
        cx=self.SW//2; yb=self.SH-55
        bar_w=6; gap=3
        total=len(self.speak_bars)*(bar_w+gap); start=cx-total//2
        for i,h in enumerate(self.speak_bars):
            bh=max(2,int(h*38)); bx=start+i*(bar_w+gap); by=yb-bh//2
            a=int(190*h*alpha)
            g=QLinearGradient(bx,by,bx,by+bh)
            g.setColorAt(0,QColor(0,230,180,a)); g.setColorAt(1,QColor(0,150,230,a))
            p.fillRect(int(bx),int(by),bar_w,bh,QBrush(g))

    def _draw_notifications(self, p):
        for i,n in enumerate(self.notifications[-3:]):
            a=n['alpha']; x=self.SW-310; y=self.SH-150-i*55
            self._panel(p,x,y,290,40,a*0.7)
            p.setFont(QFont("Consolas",9))
            p.setPen(QPen(QColor(0,210,230,int(210*a)),1))
            p.drawText(int(x+10),int(y+25),n['text'])

    def _draw_horizon(self, p, alpha):
        a=int(35*alpha); cy=self.SH//2; w=180
        gl=QLinearGradient(0,cy,w,cy)
        gl.setColorAt(0,QColor(0,210,230,0)); gl.setColorAt(1,QColor(0,210,230,a))
        p.fillRect(0,cy-1,w,2,QBrush(gl))
        gr=QLinearGradient(self.SW-w,cy,self.SW,cy)
        gr.setColorAt(0,QColor(0,210,230,a)); gr.setColorAt(1,QColor(0,210,230,0))
        p.fillRect(self.SW-w,cy-1,w,2,QBrush(gr))