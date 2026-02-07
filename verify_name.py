import sys
import os
import json
import time

# Mock dependencies to avoid starting full engine
sys.path.append(os.getcwd())

# Mock Speaker and Listener
class MockSpeaker:
    def __init__(self, status_queue=None):
        self.is_speaking_flag = None
    def speak(self, text, blocking=True):
        print(f"MOCK SPEAKER: {text}")
    def terminate(self):
        pass

class MockListener:
    def __init__(self, status_queue=None, is_speaking_flag=None):
        pass
    def update_keywords(self, vocab):
        print(f"MOCK LISTENER: Updated keywords with length {len(vocab)}")
    def listen(self):
        return None

# Mock NLU
class MockNLU:
    def __init__(self):
        pass
    def get_vocabulary_phrase(self):
        return ""
    def predict(self, text):
        return "unknown", 0.0

# Mock imports in engine.py
import core.engine
core.engine.Speaker = MockSpeaker
core.engine.Listener = MockListener
core.engine.NeuralIntentModel = MockNLU

from core.engine import CortexEngine

def test_name_customization():
    print("--- Testing Name Customization ---")
    
    # 1. Reset Config
    config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')
    with open(config_path, 'w') as f:
        json.dump({"name": "TestUser"}, f)
    
    # 2. Initialize Engine
    engine = CortexEngine()
    
    # Verify initial name load
    print(f"Initial Name in Config: {engine.user_config['name']}")
    assert engine.user_config['name'] == "TestUser"
    
    # 3. Test Greeting
    print("\n--- Testing Greeting ---")
    engine.greet_user()
    
    # 4. Test Change Name
    print("\n--- Testing Change Name Intent ---")
    engine.execute_intent('change_name', 'call me Commander')
    
    # Verify name update in memory
    print(f"New Name in Memory: {engine.user_config['name']}")
    assert engine.user_config['name'] == "Commander"
    
    # Verify persistence
    with open(config_path, 'r') as f:
        saved_config = json.load(f)
    print(f"Saved Name on Disk: {saved_config['name']}")
    assert saved_config['name'] == "Commander"
    
    # 5. Test Exit Message
    print("\n--- Testing Exit Message ---")
    engine.execute_intent('exit', 'exit')

    # 6. Test Date (GeneralEngine)
    print("\n--- Testing GeneralEngine Date ---")
    engine.execute_intent('date', 'date')

    print("\n--- Verification Passed ---")

if __name__ == "__main__":
    test_name_customization()
