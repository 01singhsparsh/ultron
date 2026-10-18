import cv2
import numpy as np
import time
import math

class HolographicRenderer:
    def __init__(self, width, height):
        self.w=width;self.h=height;self.t=0.0
        self.cyan=(230,210,0);self.blue=(255,150,0);self.draw_color=(255,255,0)

    def _glow(self, frame, x, y, w, h, color, thickness=2, alpha=0.5):
        overlay = frame.copy()
        for i in range(4,0,-1):
            c = tuple(int(ch*i/4) for ch in color)
            cv2.rectangle(overlay,(int(x)-i*2,int(y)-i*2),(int(x+w)+i*2,int(y+h)+i*2),c,thickness+i)
        cv2.addWeighted(overlay,alpha,frame,1-alpha*0.5,0,frame)
        cv2.rectangle(frame,(int(x),int(y)),(int(x+w),int(y+h)),color,thickness)

    def _draw_panel(self, frame, x, y, w, h, title, content=None, color=None):
        if color is None: color=self.cyan
        x,y,w,h=int(x),int(y),int(w),int(h)
        overlay=frame.copy()
        cv2.rectangle(overlay,(x,y),(x+w,y+h),(25,12,0),-1)
        cv2.addWeighted(overlay,0.4,frame,0.6,0,frame)
        self._glow(frame,x,y,w,h,color)
        corner=16
        for (cx,cy,dx,dy) in [(x,y,1,1),(x+w,y,-1,1),(x,y+h,1,-1),(x+w,y+h,-1,-1)]:
            cv2.line(frame,(cx,cy),(cx+dx*corner,cy),color,2)
            cv2.line(frame,(cx,cy),(cx,cy+dy*corner),color,2)
        cv2.rectangle(frame,(x,y),(x+w,y+28),color,-1)
        cv2.putText(frame,title,(x+8,y+20),cv2.FONT_HERSHEY_SIMPLEX,0.55,(0,0,0),2)
        scan_y=y+28+int((h-28)*((math.sin(self.t*2)+1)/2))
        if 0<=scan_y-y<=h: cv2.line(frame,(x,scan_y),(x+w,scan_y),color,1)
        if content:
            for i,line in enumerate(content.split('\n')[:6]):
                cy=y+50+i*22
                if cy<y+h-5: cv2.putText(frame,line[:44],(x+8,cy),cv2.FONT_HERSHEY_SIMPLEX,0.42,color,1)

    def _draw_strokes(self, frame, strokes, current_stroke):
        overlay=frame.copy()
        for stroke in strokes:
            for i in range(1,len(stroke)): cv2.line(overlay,stroke[i-1],stroke[i],self.draw_color,3)
        if len(current_stroke)>1:
            for i in range(1,len(current_stroke)): cv2.line(overlay,current_stroke[i-1],current_stroke[i],(0,255,255),4)
        cv2.addWeighted(overlay,0.85,frame,0.15,0,frame)
        for stroke in strokes:
            for i in range(1,len(stroke)): cv2.line(frame,stroke[i-1],stroke[i],self.draw_color,2)
        if len(current_stroke)>1:
            for i in range(1,len(current_stroke)): cv2.line(frame,current_stroke[i-1],current_stroke[i],(0,255,255),2)

    def _draw_hud(self, frame, hands_data, gestures, draw_mode):
        cv2.rectangle(frame,(0,0),(self.w,35),(30,15,0),-1)
        t_str=time.strftime("%H:%M:%S"); mode_txt="DRAW MODE" if draw_mode else "GRAB MODE"
        cv2.putText(frame,f"ULTRON PIPELINE  |  {t_str}  |  {mode_txt}",(10,24),cv2.FONT_HERSHEY_SIMPLEX,0.6,self.cyan,1)
        cv2.putText(frame,f"HANDS: {len(hands_data)}",(self.w-260,24),cv2.FONT_HERSHEY_SIMPLEX,0.5,self.cyan,1)
        if gestures:
            gname=gestures[0]['name'].upper().replace('_',' ')
            cv2.putText(frame,f"GESTURE: {gname}",(10,self.h-15),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,100),1)
        cv2.rectangle(frame,(0,self.h-30),(self.w,self.h),(30,15,0),-1)
        cv2.putText(frame,"PINCH=GRAB/DRAW | OPEN PALM=MENU | FIST=CLOSE | D=DRAW | C=CLEAR | Q=QUIT",
                   (10,self.h-10),cv2.FONT_HERSHEY_SIMPLEX,0.35,self.cyan,1)

    def _draw_fingertips(self, frame, hands_data, pinching_hands):
        for idx, hand in enumerate(hands_data):
            lm=hand['landmarks']; is_pinch=idx in pinching_hands
            color=(0,255,255) if is_pinch else self.cyan
            for tip_id in [4,8,12,16,20]:
                x=int(lm[tip_id]['x']); y=int(lm[tip_id]['y'])
                overlay=frame.copy()
                cv2.circle(overlay,(x,y),10,color,-1)
                cv2.addWeighted(overlay,0.25,frame,0.75,0,frame)
                cv2.circle(frame,(x,y),4,color,-1)
            if is_pinch:
                tx,ty=int(lm[4]['x']),int(lm[4]['y']); ix,iy=int(lm[8]['x']),int(lm[8]['y'])
                cv2.line(frame,(tx,ty),(ix,iy),(0,255,255),2)

    def render(self, frame, panels, hands_data, gestures, strokes, current_stroke, draw_mode, pinching_hands):
        self.t+=0.05
        overlay=frame.copy()
        cv2.addWeighted(overlay,0.7,np.zeros_like(frame),0.3,0,frame)
        for name, panel in panels.items():
            obj=panel.get('physics')
            if obj: self._draw_panel(frame,obj.x,obj.y,obj.w,obj.h,panel.get('title',name),panel.get('content',''),panel.get('color',self.cyan))
        self._draw_strokes(frame,strokes,current_stroke)
        self._draw_fingertips(frame,hands_data,pinching_hands)
        self._draw_hud(frame,hands_data,gestures,draw_mode)
        return frame