import psutil, datetime, platform
from pipeline.physics_engine import PhysicsEngine

class Workspace:
    def __init__(self, screen_w, screen_h):
        self.w=screen_w;self.h=screen_h
        self.physics=PhysicsEngine(screen_w,screen_h)
        self.panels={};self.grabbed_panel=None;self.prev_scale_dist=None
        self.draw_mode=False;self.strokes=[];self.current_stroke=[]
        self.colors={'default':(230,210,0),'green':(50,220,50),'red':(50,50,220),'purple':(220,50,200),'orange':(30,160,255)}

    def spawn_panel(self, name, title, x=None, y=None, w=320, h=200, color=None, content=''):
        if x is None: x=self.w//2-w//2
        if y is None: y=self.h//2-h//2
        self.physics.add_object(name,x,y,w,h)
        self.panels[name]={'title':title,'content':content,'color':color or self.colors['default'],'physics':self.physics.objects[name]}

    def close_panel(self, name):
        if name in self.panels:
            del self.panels[name]; self.physics.remove_object(name)

    def spawn_default_panels(self):
        self.spawn_panel('system','SYSTEM MONITOR',x=20,y=50,w=280,h=180,color=self.colors['green'])
        self.spawn_panel('chat','ULTRON CHAT',x=320,y=50,w=380,h=220,color=self.colors['default'])
        self.spawn_panel('clock','TIME & DATE',x=20,y=250,w=280,h=100,color=self.colors['purple'])
        self.spawn_panel('help','CONTROLS',x=20,y=370,w=280,h=160,color=self.colors['orange'],
                        content="PINCH: grab/draw\nOPEN PALM: menu\nFIST: close panel\nSWIPE: new panel\nD: toggle draw\nC: clear drawing")

    def update_system_panel(self):
        if 'system' in self.panels:
            try:
                cpu=psutil.cpu_percent(); ram=psutil.virtual_memory(); disk=psutil.disk_usage('/')
                batt=psutil.sensors_battery(); b=f"{int(batt.percent)}%" if batt else "N/A"
                self.panels['system']['content']=f"CPU:  {cpu}%\nRAM:  {ram.percent}%\nDISK: {disk.percent}%\nBATT: {b}\nOS:   {platform.system()}"
            except: pass

    def update_clock_panel(self):
        if 'clock' in self.panels:
            now=datetime.datetime.now()
            self.panels['clock']['content']=f"{now.strftime('%I:%M:%S %p')}\n{now.strftime('%A, %d %B %Y')}"

    def update_chat_panel(self, message='', response=''):
        if 'chat' in self.panels and (message or response):
            self.panels['chat']['content']=f"You: {message[:40]}\nULTRON: {response[:150]}"

    def handle_pinch(self, px, py, just_started):
        if self.draw_mode:
            if just_started: self.current_stroke=[(int(px),int(py))]
            else:            self.current_stroke.append((int(px),int(py)))
            return
        if self.grabbed_panel:
            obj=self.physics.objects.get(self.grabbed_panel)
            if obj: obj.move(px,py)
        elif just_started:
            name,obj=self.physics.get_object_at(px,py)
            if obj: obj.grab(px,py); self.grabbed_panel=name

    def handle_pinch_end(self):
        if self.draw_mode and len(self.current_stroke)>1: self.strokes.append(self.current_stroke)
        self.current_stroke=[]
        if self.grabbed_panel:
            obj=self.physics.objects.get(self.grabbed_panel)
            if obj: obj.release()
            self.grabbed_panel=None

    def clear_drawing(self): self.strokes=[]; self.current_stroke=[]
    def toggle_draw_mode(self): self.draw_mode=not self.draw_mode; return self.draw_mode

    def handle_scale(self, dist):
        if self.prev_scale_dist and self.grabbed_panel:
            obj=self.physics.objects.get(self.grabbed_panel)
            if obj:
                ratio=dist/(self.prev_scale_dist+0.001)
                obj.w=max(200,min(600,obj.w*ratio)); obj.h=max(100,min(400,obj.h*ratio))
        self.prev_scale_dist=dist

    def update(self): self.physics.update(); self.update_system_panel(); self.update_clock_panel()