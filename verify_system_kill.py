from core.engines.system import SystemEngine
import subprocess
import time

class MockSpeaker:
    def speak(self, text, blocking=True):
        print(f"Speaker: {text}")

class MockListener:
    def listen(self):
        print("Listener: (Simulating 'yes')")
        return "yes"

speaker = MockSpeaker()
listener = MockListener()
system = SystemEngine(speaker, listener)

print("--- Testing SystemEngine Kill Logic ---")

# 1. Start Notepad
print("Starting Notepad...")
subprocess.Popen("notepad.exe")
time.sleep(2)

# 2. Kill Notepad using SystemEngine
print("Requesting: 'kill notepad'")
# Note: _kill_process expects the command string
system._kill_process("kill notepad")

# 3. Requesting kill chrome (not open)
print("Requesting: 'close chrome'")
system._kill_process("close chrome")
