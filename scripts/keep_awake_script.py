import pyautogui
import time
import sys

# Move mouse 1 pixel every 60 seconds to prevent sleep
try:
    while True:
        pyautogui.moveRel(1, 0)
        pyautogui.moveRel(-1, 0)
        time.sleep(60)
except KeyboardInterrupt:
    sys.exit()