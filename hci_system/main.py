# main.py

import cv2
import numpy as np
import pyautogui
import mediapipe as mp
from utils.gesture_utils import map_to_screen

def hand_gesture_mouse_control():
    cap = cv2.VideoCapture(0)

    hand_detector = mp.solutions.hands.Hands()
    drawing_utils = mp.solutions.drawing_utils

    screen_w, screen_h = pyautogui.size()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame_h, frame_w, _ = frame.shape

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output = hand_detector.process(rgb_frame)

        hands = output.multi_hand_landmarks
        if hands:
            for hand in hands:
                drawing_utils.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)

                landmarks = hand.landmark
                index_finger = landmarks[8]
                x = int(index_finger.x * frame_w)
                y = int(index_finger.y * frame_h)

                screen_x, screen_y = map_to_screen(x, y, frame_w, frame_h)
                pyautogui.moveTo(screen_x, screen_y)

                cv2.circle(frame, (x, y), 10, (0, 255, 255), -1)

        cv2.imshow('Hand Control', frame)
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

# 🚫 DO NOT CALL THE FUNCTION HERE
# hand_gesture_mouse_control()
