import numpy as np
import time

class PhysicsObject:
    def __init__(self, x, y, w, h):
        self.x=float(x);self.y=float(y);self.w=float(w);self.h=float(h)
        self.vx=0.0;self.vy=0.0;self.scale=1.0;self.rotation=0.0
        self.damping=0.85;self.grabbed=False;self.grab_dx=0.0;self.grab_dy=0.0
        self.prev_time=time.time()

    def grab(self, px, py):
        self.grabbed=True;self.grab_dx=px-self.x;self.grab_dy=py-self.y;self.vx=0;self.vy=0

    def move(self, px, py):
        if self.grabbed:
            now=time.time();dt=now-self.prev_time+0.001
            new_x=px-self.grab_dx;new_y=py-self.grab_dy
            self.vx=(new_x-self.x)/dt;self.vy=(new_y-self.y)/dt
            self.x=new_x;self.y=new_y;self.prev_time=now

    def release(self): self.grabbed=False

    def update(self, screen_w, screen_h):
        if not self.grabbed:
            self.x+=self.vx*0.016;self.y+=self.vy*0.016
            self.vx*=self.damping;self.vy*=self.damping
            if self.x < 0:              self.x=0;self.vx=abs(self.vx)*0.5
            if self.y < 0:              self.y=0;self.vy=abs(self.vy)*0.5
            if self.x+self.w>screen_w:  self.x=screen_w-self.w;self.vx=-abs(self.vx)*0.5
            if self.y+self.h>screen_h:  self.y=screen_h-self.h;self.vy=-abs(self.vy)*0.5

    def contains(self, px, py):
        return self.x < px < self.x+self.w and self.y < py < self.y+self.h

class PhysicsEngine:
    def __init__(self, screen_w, screen_h):
        self.screen_w=screen_w;self.screen_h=screen_h;self.objects={}

    def add_object(self, name, x, y, w, h): self.objects[name]=PhysicsObject(x,y,w,h)
    def remove_object(self, name):
        if name in self.objects: del self.objects[name]

    def update(self):
        for obj in self.objects.values(): obj.update(self.screen_w, self.screen_h)

    def get_object_at(self, px, py):
        for name, obj in self.objects.items():
            if obj.contains(px, py): return name, obj
        return None, None