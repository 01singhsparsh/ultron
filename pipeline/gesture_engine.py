import numpy as np
import time

class GestureEngine:
    def __init__(self):
        self.last_gesture = {}
        self.gesture_time = {}
        self.cooldown     = 0.5
        self.pinch_state  = {}

    def _finger_extended(self, lm, finger):
        tips = {'index':8,'middle':12,'ring':16,'pinky':20,'thumb':4}
        mids = {'index':6,'middle':10,'ring':14,'pinky':18,'thumb':2}
        tip  = tips[finger]; mid = mids[finger]
        if finger == 'thumb': return abs(lm[tip]['x']-lm[0]['x']) > abs(lm[mid]['x']-lm[0]['x'])
        return lm[tip]['y'] < lm[mid]['y'] - 5

    def _pinch_distance(self, lm):
        t = lm[4]; i = lm[8]
        return np.sqrt((t['x']-i['x'])**2 + (t['y']-i['y'])**2)

    def _all_fingers_extended(self, lm):
        return all(self._finger_extended(lm,f) for f in ['index','middle','ring','pinky'])

    def _all_fingers_closed(self, lm):
        return all(not self._finger_extended(lm,f) for f in ['index','middle','ring','pinky'])

    def recognize(self, hand):
        lm = hand['landmarks']; label = hand['label']; now = time.time(); gestures = []
        pinch_dist   = self._pinch_distance(lm)
        pinch_thresh = max(25, min(60, hand['hand_size'] * 0.30))
        is_pinching  = pinch_dist < pinch_thresh
        was_pinching = self.pinch_state.get(label, False)
        self.pinch_state[label] = is_pinching
        pinch_x = (lm[4]['x'] + lm[8]['x']) / 2
        pinch_y = (lm[4]['y'] + lm[8]['y']) / 2
        if is_pinching:
            gestures.append({'name':'pinch','confidence':1.0,'position':(pinch_x,pinch_y),'just_started':not was_pinching})
        if self._all_fingers_extended(lm):
            gestures.append({'name':'open_palm','confidence':0.9,'position':hand['palm']})
        if self._all_fingers_closed(lm) and not is_pinching:
            gestures.append({'name':'fist','confidence':0.9,'position':hand['palm']})
        index_ext  = self._finger_extended(lm,'index')
        middle_ext = self._finger_extended(lm,'middle')
        ring_ext   = self._finger_extended(lm,'ring')
        pinky_ext  = self._finger_extended(lm,'pinky')
        if index_ext and not middle_ext and not ring_ext and not pinky_ext:
            gestures.append({'name':'point','confidence':0.95,'position':(lm[8]['x'],lm[8]['y'])})
        vx, vy = hand['velocity']; speed = np.sqrt(vx**2+vy**2)
        if speed > 400 and not is_pinching:
            if abs(vx) > abs(vy):
                direction = 'swipe_right' if vx > 0 else 'swipe_left'
                last = self.last_gesture.get(label); last_t = self.gesture_time.get(label,0)
                if direction != last or now - last_t > self.cooldown:
                    gestures.append({'name':direction,'confidence':0.85,'position':hand['palm']})
                    self.last_gesture[label] = direction; self.gesture_time[label] = now
        return gestures

    def recognize_two_hands(self, hands):
        if len(hands) < 2: return []
        h1, h2 = hands[0], hands[1]
        lm1, lm2 = h1['landmarks'], h2['landmarks']; gestures = []
        p1 = self._pinch_distance(lm1); p2 = self._pinch_distance(lm2)
        th1 = max(25,min(60,h1['hand_size']*0.30)); th2 = max(25,min(60,h2['hand_size']*0.30))
        if p1 < th1 and p2 < th2:
            t1x,t1y = lm1[4]['x'],lm1[4]['y']; t2x,t2y = lm2[4]['x'],lm2[4]['y']
            dist = np.sqrt((t1x-t2x)**2+(t1y-t2y)**2)
            gestures.append({'name':'two_hand_pinch','confidence':0.9,'scale_distance':dist,'midpoint':((t1x+t2x)/2,(t1y+t2y)/2)})
        return gestures