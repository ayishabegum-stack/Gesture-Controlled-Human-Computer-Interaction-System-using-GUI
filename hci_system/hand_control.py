import cv2
import numpy as np
import pyautogui
import mediapipe as mp
import time
import pyttsx3  # 🔈 For voice feedback

from utils.gesture_utils import map_to_screen, calculate_distance

# Volume control imports
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

# Initialize TTS engine
engine = pyttsx3.init()
engine.setProperty('rate', 160)  # Optional: set speech rate

# Initialize webcam
cap = cv2.VideoCapture(0)

# Initialize MediaPipe Hands
hand_detector = mp.solutions.hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.8,
    min_tracking_confidence=0.8
)
drawing_utils = mp.solutions.drawing_utils

# Get frame and screen dimensions
frame_w = int(cap.get(3))
frame_h = int(cap.get(4))   
screen_w, screen_h = pyautogui.size()

# Gesture thresholds and timings
LEFT_CLICK_THRESHOLD = 40
DRAG_HOLD_TIME = 1.2
SCROLL_COOLDOWN = 0.3
SCROLL_UP_THRESHOLD = int(frame_h * 0.4)
SCROLL_DOWN_THRESHOLD = int(frame_h * 0.6)
SCROLL_AMOUNT = 100

# State variables
left_pinch_active = False
drag_active = False
pinch_start_time = 0
last_scroll_time = 0

# Palm detection tracking
palm_detected_count = 0
PALM_FRAMES_THRESHOLD = 15

# Initialize volume control
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume_ctrl = cast(interface, POINTER(IAudioEndpointVolume))

print("🟢 Hand gesture control with palm-exit started...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hand_detector.process(rgb_frame)
    hands = results.multi_hand_landmarks

    if hands:
        for hand in hands:
            drawing_utils.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)
            landmarks = hand.landmark

            tip_ids = [4, 8, 12, 16, 20]
            pip_ids = [3, 6, 10, 14, 18]
            fingers_up = [landmarks[tip_ids[i]].y < landmarks[pip_ids[i]].y for i in range(5)]

            if all(fingers_up):
                palm_detected_count += 1
                cv2.putText(frame, "👋 Palm Detected - Exiting...", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                if palm_detected_count >= PALM_FRAMES_THRESHOLD:
                    print("👋 Palm detected for multiple frames. Exiting...")
                    engine.say("Exiting hand gesture control")
                    engine.runAndWait()
                    cap.release()
                    cv2.destroyAllWindows()
                    exit()
            else:
                palm_detected_count = 0

            # Landmark positions
            index_tip = landmarks[8]
            thumb_tip = landmarks[4]
            thumb_mcp = landmarks[2]
            middle_tip = landmarks[12]

            ix = int(index_tip.x * frame_w)
            iy = int(index_tip.y * frame_h)
            tx = int(thumb_tip.x * frame_w)
            ty = int(thumb_tip.y * frame_h)
            mx = int(middle_tip.x * frame_w)
            my = int(middle_tip.y * frame_h)

            screen_x, screen_y = map_to_screen(ix, iy, frame_w, frame_h)
            pyautogui.moveTo(screen_x, screen_y, duration=0.05)
            cv2.circle(frame, (ix, iy), 8, (0, 255, 255), -1)

            # Left click / drag
            distance_left = calculate_distance((ix, iy), (tx, ty))
            if distance_left < LEFT_CLICK_THRESHOLD:
                if not left_pinch_active:
                    left_pinch_active = True
                    pinch_start_time = time.time()
                else:
                    hold_duration = time.time() - pinch_start_time
                    if hold_duration > DRAG_HOLD_TIME and not drag_active:
                        pyautogui.mouseDown()
                        drag_active = True
                        print("Drag started")
            else:
                if left_pinch_active:
                    hold_duration = time.time() - pinch_start_time
                    if drag_active:
                        pyautogui.mouseUp()
                        drag_active = False
                        print("Drag ended")
                    elif hold_duration < DRAG_HOLD_TIME:
                        pyautogui.click()
                        print("Single Click")
                    left_pinch_active = False

            # Scroll logic
            current_time = time.time()
            if current_time - last_scroll_time > SCROLL_COOLDOWN and not left_pinch_active:
                if my < SCROLL_UP_THRESHOLD:
                    pyautogui.scroll(SCROLL_AMOUNT)
                    last_scroll_time = current_time
                elif my > SCROLL_DOWN_THRESHOLD:
                    pyautogui.scroll(-SCROLL_AMOUNT)
                    last_scroll_time = current_time

            # Volume control
            thumb_tip_y = thumb_tip.y
            thumb_mcp_y = thumb_mcp.y

            index_folded = landmarks[8].y > landmarks[6].y
            middle_folded = landmarks[12].y > landmarks[10].y
            ring_folded = landmarks[16].y > landmarks[14].y
            pinky_folded = landmarks[20].y > landmarks[18].y

            other_fingers_folded = all([index_folded, middle_folded, ring_folded, pinky_folded])
            thumb_extended = abs(thumb_tip_y - thumb_mcp_y) > 0.05

            if other_fingers_folded and thumb_extended:
                current_volume = volume_ctrl.GetMasterVolumeLevel()
                if thumb_tip_y < thumb_mcp_y:
                    new_volume = min(current_volume + 1.5, 0.0)
                    volume_ctrl.SetMasterVolumeLevel(new_volume, None)
                    cv2.putText(frame, "🔊 Volume Up", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                elif thumb_tip_y > thumb_mcp_y:
                    new_volume = max(current_volume - 1.5, -65.25)
                    volume_ctrl.SetMasterVolumeLevel(new_volume, None)
                    cv2.putText(frame, "🔉 Volume Down", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    else:
        palm_detected_count = 0

    cv2.imshow("Hand Gesture Mouse Control", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
