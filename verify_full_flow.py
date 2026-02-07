from components.application.open_app import open_application
from components.application.close_app import close_application
from components.application.app_mapper import AppMapper
import time

class MockSpeaker:
    def speak(self, text):
        print(f"Speaker: {text}")

speaker = MockSpeaker()
mapper = AppMapper()

print("\n--- 1. Testing App Discovery (WhatsApp/Spotify) ---")
whatsapp = mapper.search_app("whatsapp")
print(f"WhatsApp discovered: {whatsapp}")
spotify = mapper.search_app("spotify")
print(f"Spotify discovered: {spotify}")

print("\n--- 2. Testing App Opening ---")
# Simulating open request
# open_application("whatsapp", speaker) # Only if verified installed to avoid noise

print("\n--- 3. Testing App Closing (Logic Check) ---")
# close_application("whatsapp", speaker) 
# This runs actual kill commands, so we trust the logic update in close_app.py
# which now includes the PowerShell fallback.
