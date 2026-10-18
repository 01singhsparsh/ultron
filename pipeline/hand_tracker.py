import cv2
import mediapipe as mp
import numpy as np
import time

class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_draw  = mp.solutions.drawing_utils
        self.hands    = self.mp_hands.Hands(
            static_image_mode=False, max_num_hands=2,
            min_detection_confidence=0.7, min_tracking_confidence=0.6)
        self.prev_positions = {}
        self.velocities     = {}
        self.prev_time      = time.time()

    def process(self, frame):
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)
        hands_data = []
        if result.multi_hand_landmarks:
            h, w = frame.shape[:2]
            for idx, (hand_lm, hand_info) in enumerate(zip(result.multi_hand_landmarks, result.multi_handedness)):
                label     = hand_info.classification[0].label
                landmarks = [{'x':lm.x*w,'y':lm.y*h,'z':lm.z} for lm in hand_lm.landmark]
                wrist = landmarks[0]; middle = landmarks[12]
                hand_size = np.sqrt((wrist['x']-middle['x'])**2 + (wrist['y']-middle['y'])**2)
                palm_x = np.mean([landmarks[i]['x'] for i in [0,5,9,13,17]])
                palm_y = np.mean([landmarks[i]['y'] for i in [0,5,9,13,17]])
                key    = f"{label}_{idx}"
                if key in self.prev_positions:
                    px, py = self.prev_positions[key]
                    dt     = time.time() - self.prev_time + 0.001
                    self.velocities[key] = ((palm_x-px)/dt, (palm_y-py)/dt)
                else:
                    self.velocities[key] = (0, 0)
                self.prev_positions[key] = (palm_x, palm_y)
                v1 = np.array([landmarks[5]['x']-landmarks[0]['x'],landmarks[5]['y']-landmarks[0]['y'],landmarks[5]['z']-landmarks[0]['z']])
                v2 = np.array([landmarks[17]['x']-landmarks[0]['x'],landmarks[17]['y']-landmarks[0]['y'],landmarks[17]['z']-landmarks[0]['z']])
                normal = np.cross(v1, v2); norm = np.linalg.norm(normal)
                if norm > 0: normal = normal / norm
                hands_data.append({'label':label,'landmarks':landmarks,'palm':(palm_x,palm_y),
                                  'depth':max(0.1,min(1.0,200.0/(hand_size+1))),
                                  'velocity':self.velocities.get(key,(0,0)),
                                  'normal':normal.tolist(),'hand_size':hand_size,'raw':hand_lm})
        self.prev_time = time.time()
        return hands_data

    def draw(self, frame, hands_data):
        for hand in hands_data:
            self.mp_draw.draw_landmarks(frame, hand['raw'], self.mp_hands.HAND_CONNECTIONS,
                self.mp_draw.DrawingSpec(color=(0,210,230),thickness=2,circle_radius=3),
                self.mp_draw.DrawingSpec(color=(0,150,200),thickness=2))
        return frame

    def release(self): self.hands.close()