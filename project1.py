import cv2
import numpy as np
import mediapipe as mp
import screen_brightness_control as sbc
from math import hypot
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import *
from comtypes import *
import pyautogui
import os
import time

# Shared file for mode communication
MODE_FILE = "mode.txt"

def main():
    # Initialize mode
    mode = "brightness"

    # Initialize mediapipe hands
    mpHands = mp.solutions.hands
    hands = mpHands.Hands(min_detection_confidence=0.75, min_tracking_confidence=0.75, max_num_hands=2)
    draw = mp.solutions.drawing_utils

    # Initialize camera
    cap = cv2.VideoCapture(0)
    cv2.namedWindow('GesturePilot - Gesture Control System', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('GesturePilot - Gesture Control System', 1280, 720)

    # Initialize volume control
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volRange = volume.GetVolumeRange()
    minVol, maxVol, _ = volRange

    # Variables for screenshot feature
    last_screenshot_time = 0
    screenshot_interval = 5  # Minimum interval between screenshots (in seconds)

    # Variables for scroll feature
    scroll_active = False
    last_scroll_time = 0

    try:
        while cap.isOpened():
            # Read the current mode from the shared file
            with open(MODE_FILE, "r") as f:
                mode = f.read().strip()

            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            processed = hands.process(frameRGB)

            landmark_data = get_landmarks(frame, processed, draw, mpHands)
            for hand_label, landmark_list in landmark_data.items():
                if hand_label == "Left" and landmark_list:
                    distance = get_distance(frame, landmark_list)
                    if mode == "brightness":
                        b_level = np.interp(distance, [50, 220], [0, 100])
                        sbc.set_brightness(int(b_level))
                        draw_bar(frame, 50, 50, 300, int(b_level), (255, 255, 0), "Brightness")
                        draw_line_between_fingers(frame, landmark_list)

                elif hand_label == "Right" and landmark_list:
                    distance = get_distance(frame, landmark_list)
                    if mode == "volume":
                        vol = np.interp(distance, [50, 220], [minVol, maxVol])
                        volume.SetMasterVolumeLevel(vol, None)
                        vol_percentage = np.interp(vol, [minVol, maxVol], [0, 100])
                        draw_bar(frame, 50, 50, 300, int(vol_percentage), (0, 255, 0), "Volume")
                        draw_line_between_fingers(frame, landmark_list)
                    elif mode == "zoom":
                        zoom_action(distance)
                    elif mode == "media":
                        if check_thumb_index_touch(landmark_list):
                            pyautogui.press('space')
                            time.sleep(0.5)
                    elif mode == "mouse":
                        control_mouse(landmark_list)
                    elif mode == "screenshot":
                        if check_index_up(landmark_list):
                            current_time = time.time()
                            if current_time - last_screenshot_time >= screenshot_interval:
                                take_screenshot()
                                last_screenshot_time = current_time
                    elif mode == "scroll":
                        if check_thumb_index_touch(landmark_list):
                            if not scroll_active:
                                scroll_active = True
                                last_scroll_time = time.time()
                            elif time.time() - last_scroll_time >= 0.02:  # Faster scroll (0.02 seconds)
                                # Detect scroll direction (up or down)
                                if landmark_list[0][2] < landmark_list[1][2]:  # Scroll down
                                    pyautogui.scroll(-100)  # Scroll down
                                else:  # Scroll up
                                    pyautogui.scroll(100)  # Scroll up
                                last_scroll_time = time.time()
                        else:
                            scroll_active = False
                    elif mode == "switcher":
                        if check_thumb_index_touch(landmark_list):
                            pyautogui.hotkey('alt', 'tab')  # Switch between open applications
                            time.sleep(0.5)

            cv2.putText(frame, f"Mode: {mode}", (50, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.imshow('GesturePilot - Gesture Control System', frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

def get_landmarks(frame, processed, draw, mpHands):
    landmark_data = {}
    if processed.multi_handedness and processed.multi_hand_landmarks:
        for hand_handedness, hand_landmarks in zip(processed.multi_handedness, processed.multi_hand_landmarks):
            hand_label = hand_handedness.classification[0].label
            landmark_list = [(idx, int(landmark.x * frame.shape[1]), int(landmark.y * frame.shape[0])) for idx, landmark in enumerate(hand_landmarks.landmark) if idx in [4, 8, 12]]
            landmark_data[hand_label] = landmark_list
            draw.draw_landmarks(frame, hand_landmarks, mpHands.HAND_CONNECTIONS)
    return landmark_data

def get_distance(frame, landmark_list):
    if len(landmark_list) < 2:
        return 0
    (x1, y1), (x2, y2) = landmark_list[0][1:], landmark_list[1][1:]
    return hypot(x2 - x1, y2 - y1)

def draw_line_between_fingers(frame, landmark_list):
    x1, y1 = landmark_list[0][1], landmark_list[0][2]
    x2, y2 = landmark_list[1][1], landmark_list[1][2]
    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 255), 3)

def control_mouse(landmark_list):
    x, y = landmark_list[1][1], landmark_list[1][2]
    screen_x, screen_y = pyautogui.size()
    pyautogui.moveTo(screen_x * (x / 1280), screen_y * (y / 720))
    if hypot(landmark_list[2][1] - landmark_list[1][1], landmark_list[2][2] - landmark_list[1][2]) < 30:
        pyautogui.click()

def zoom_action(distance):
    if distance > 150:
        pyautogui.hotkey('ctrl', '-')
    elif distance < 100:
        pyautogui.hotkey('ctrl', '+')

def draw_bar(frame, x, y, width, percentage, color, label=""):
    bar_height = 20
    filled_width = int((percentage / 100) * width)
    cv2.rectangle(frame, (x, y), (x + width, y + bar_height), (200, 200, 200), -1)
    cv2.rectangle(frame, (x, y), (x + filled_width, y + bar_height), color, -1)
    cv2.putText(frame, f'{label}: {percentage}%', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def check_thumb_index_touch(landmark_list):
    if len(landmark_list) < 2:
        return False
    (x1, y1), (x2, y2) = landmark_list[0][1:], landmark_list[1][1:]
    return hypot(x2 - x1, y2 - y1) < 30

def check_index_up(landmark_list):
    if len(landmark_list) < 2:
        return False
    (x1, y1), (x2, y2) = landmark_list[0][1:], landmark_list[1][1:]
    return y1 > y2 and abs(x1 - x2) < 50

def take_screenshot():
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(f"mpr_pics/screenshot_{int(time.time())}.png")
    except Exception as e:
        print(f"Error taking screenshot: {e}")

if __name__ == '__main__':
    main()