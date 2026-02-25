import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
from collections import deque
import pyttsx3

# Voice setup
engine = pyttsx3.init()
engine.setProperty('rate', 160)
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Setup
screen_w, screen_h = pyautogui.size()
cap = cv2.VideoCapture(0)
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)

# Config
BASE_SENSITIVITY = 65
ALPHA = 0.1
SMOOTHING_BUFFER = 8
DEAD_ZONE = 25
cursor_x, cursor_y = screen_w // 2, screen_h // 2
eye_ref_x, eye_ref_y = None, None
eye_buffer_x = deque(maxlen=SMOOTHING_BUFFER)
eye_buffer_y = deque(maxlen=SMOOTHING_BUFFER)

# Blink detection
BLINK_THRESHOLD = 0.22
CONSEC_FRAMES = 2
blink_counter = 0
blink_timestamps = []
DOUBLE_CLICK_TIME = 0.5

# Scroll hold blink
SCROLL_HOLD_FRAMES = 12
scroll_up_counter = 0
scroll_down_counter = 0

# Landmark indices
RIGHT_EYE_TOP = 159
RIGHT_EYE_BOTTOM = 145
RIGHT_EYE_LEFT = 33
RIGHT_EYE_RIGHT = 133

LEFT_EYE_TOP = 386
LEFT_EYE_BOTTOM = 374
LEFT_EYE_LEFT = 263
LEFT_EYE_RIGHT = 362

RIGHT_IRIS = 474

UPPER_LIP = 13
LOWER_LIP = 14
MOUTH_OPEN_THRESHOLD = 20  # Adjust if needed

def calculate_ear(landmarks, top_idx, bottom_idx, left_idx, right_idx, w, h):
    top = np.array([landmarks[top_idx].x * w, landmarks[top_idx].y * h])
    bottom = np.array([landmarks[bottom_idx].x * w, landmarks[bottom_idx].y * h])
    left = np.array([landmarks[left_idx].x * w, landmarks[left_idx].y * h])
    right = np.array([landmarks[right_idx].x * w, landmarks[right_idx].y * h])
    vertical = np.linalg.norm(top - bottom)
    horizontal = np.linalg.norm(left - right)
    return vertical / horizontal

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    key = cv2.waitKey(1) & 0xFF

    if results.multi_face_landmarks:
        face = results.multi_face_landmarks[0].landmark

        # EAR values
        ear_left = calculate_ear(face, LEFT_EYE_TOP, LEFT_EYE_BOTTOM, LEFT_EYE_LEFT, LEFT_EYE_RIGHT, w, h)
        ear_right = calculate_ear(face, RIGHT_EYE_TOP, RIGHT_EYE_BOTTOM, RIGHT_EYE_LEFT, RIGHT_EYE_RIGHT, w, h)

        # Mouth open detection for exit
        upper_lip = np.array([face[UPPER_LIP].x * w, face[UPPER_LIP].y * h])
        lower_lip = np.array([face[LOWER_LIP].x * w, face[LOWER_LIP].y * h])
        mouth_open_dist = np.linalg.norm(upper_lip - lower_lip)

        if mouth_open_dist > MOUTH_OPEN_THRESHOLD:
            cv2.putText(frame, "Mouth Open Detected - Exiting", (30, 300),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            speak("Exited from execution")
            cv2.imshow("Eye Mouse", frame)
            cv2.waitKey(1000)
            break

        # Eye tracking
        eye_x = int(face[RIGHT_IRIS].x * w)
        eye_y = int(face[RIGHT_IRIS].y * h)

        if key == ord('c'):
            eye_ref_x, eye_ref_y = eye_x, eye_y
            print("Center calibrated.")

        if eye_ref_x is not None:
            dx = (eye_x - eye_ref_x) * BASE_SENSITIVITY
            dy = (eye_y - eye_ref_y) * BASE_SENSITIVITY

            if abs(dx) > DEAD_ZONE or abs(dy) > DEAD_ZONE:
                eye_buffer_x.append(dx)
                eye_buffer_y.append(dy)

            if len(eye_buffer_x) == SMOOTHING_BUFFER:
                weights = np.linspace(1, 2, SMOOTHING_BUFFER)
                weights /= weights.sum()
                avg_dx = np.dot(eye_buffer_x, weights)
                avg_dy = np.dot(eye_buffer_y, weights)

                target_x = screen_w // 2 + avg_dx
                target_y = screen_h // 2 + avg_dy
                target_x = np.clip(target_x, 0, screen_w)
                target_y = np.clip(target_y, 0, screen_h)

                cursor_x = int((1 - ALPHA) * cursor_x + ALPHA * target_x)
                cursor_y = int((1 - ALPHA) * cursor_y + ALPHA * target_y)

                pyautogui.moveTo(cursor_x, cursor_y, duration=0)

        # Right eye hold - Volume Up
        if ear_right < BLINK_THRESHOLD:
            scroll_up_counter += 1
            if scroll_up_counter >= SCROLL_HOLD_FRAMES:
                pyautogui.press("volumeup")
                cv2.putText(frame, "Volume UP", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        else:
            scroll_up_counter = 0

        # Left eye hold - Volume Down
        if ear_left < BLINK_THRESHOLD:
            scroll_down_counter += 1
            if scroll_down_counter >= SCROLL_HOLD_FRAMES:
                pyautogui.press("volumedown")
                cv2.putText(frame, "Volume DOWN", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        else:
            scroll_down_counter = 0

        # Blink clicks
        if ear_left < BLINK_THRESHOLD:
            blink_counter += 1
        else:
            if blink_counter >= CONSEC_FRAMES:
                current_time = time.time()
                blink_timestamps.append(current_time)
                blink_timestamps = [t for t in blink_timestamps if current_time - t <= DOUBLE_CLICK_TIME]

                if len(blink_timestamps) == 2:
                    pyautogui.doubleClick()
                    cv2.putText(frame, "DOUBLE CLICK", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 100, 255), 2)
                    blink_timestamps = []
                elif len(blink_timestamps) == 1:
                    pyautogui.click()
                    cv2.putText(frame, "SINGLE CLICK", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            blink_counter = 0

        # Visuals
        cv2.circle(frame, (eye_x, eye_y), 5, (255, 255, 0), -1)
        cv2.putText(frame, "Eye Control Active", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 100), 2)

    cv2.imshow("Eye Mouse", frame)

    if key == 27:  # ESC key
        speak("Exited from execution")
        break

cap.release()
cv2.destroyAllWindows()
