from components.application.open_app import is_app_installed, open_application
import os
import sys

# Redirect stdout to a file with utf-8 encoding
sys.stdout = open("verify_output_utf8.txt", "w", encoding="utf-8")

class MockSpeaker:
    def speak(self, text):
        print(f"Speaker: {text}")

speaker = MockSpeaker()

print("--- Testing App Detection ---")
apps = ["firefox", "explorer", "chrome", "notepad", "main.py", "non_existent_app"]

for app in apps:
    exists = is_app_installed(app)
    print(f"'{app}' installed? {exists}")
    
print("\n--- Testing App Launching (Dry Run) ---")

print("Simulating 'open firefox'...")
open_application("firefox", speaker)

print("Simulating 'open main.py'...")
open_application("main.py", speaker)

print("Simulating 'open nonsense'...")
open_application("nonsense", speaker)

sys.stdout.close()
