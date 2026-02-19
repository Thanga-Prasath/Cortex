from core.engines.nlp.brain import CommandBrain
from unittest.mock import MagicMock
import os

def test_brain_integration():
    speaker = MagicMock()
    brain = CommandBrain(speaker)
    
    print("Checking model path...")
    print(f"Path: {brain.model_path}")
    print(f"Exists: {os.path.exists(brain.model_path)}")
    
    # This should fail gracefully because the model isn't downloaded yet
    print("\nAttempting to generate command (expecting failure/graceful exit)...")
    cmd = brain.generate_command("what is my ip")
    
    if cmd is None:
        print("[SUCCESS] Brain handled missing model correctly.")
    else:
        print(f"[ERROR] Brain returned: {cmd}")

if __name__ == "__main__":
    test_brain_integration()
