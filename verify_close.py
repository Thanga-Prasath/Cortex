from components.application.close_app import close_application
import subprocess
import time
import os

class MockSpeaker:
    def speak(self, text):
        print(f"Speaker: {text}")

speaker = MockSpeaker()

print("--- Testing App Close Logic ---")

# 1. Start Notepad
print("Starting Notepad...")
subprocess.Popen("notepad.exe")
time.sleep(2)

# 2. Close Notepad
print("Closing Notepad...")
close_application("notepad", speaker)

# 3. Try closing something not open
print("Closing 'nonsense'...")
close_application("nonsense", speaker)

# 4. Try closing 'chrome' (should map to chrome.exe)
# Dry run mostly unless chrome is open, but we just want to see the output trace
print("Closing 'chrome'...")
close_application("chrome", speaker)
