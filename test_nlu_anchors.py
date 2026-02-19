import sys
import os
import json
from unittest.mock import MagicMock

# Ensure we can import from core
sys.path.append(os.getcwd())

from core.nlu import NeuralIntentModel

def test_anchor_logic():
    print("Initializing NLU Model...")
    # Initialize model (this loads the updated JSONs)
    nlu = NeuralIntentModel()
    
    test_cases = [
        ("list apps", "list_apps", True),  # Should match (has 'app')
        ("list drivers", "list_apps", False), # Should NOT match list_apps (missing 'app')
        ("scan drivers", "scan_drivers", True), # Should match (has 'driver')
        ("check ip", "system_ip", True), # Should match (has 'ip')
        ("check connection", "system_ip", False) # Should NOT match system_ip (missing 'ip'/'address'/'network') - Wait, I added anchors for system_ip
    ]
    
    print("\n--- Testing Anchor Logic ---")
    
    # manual check of anchor loading
    if not hasattr(nlu, 'intent_anchors'):
        print("[FAIL] 'intent_anchors' not loaded into NLU model.")
        return

    print(f"Loaded anchors for {len(nlu.intent_anchors)} intents.")
    
    # 1. Test "list drivers" specifically
    text = "list drivers"
    print(f"\nQuery: '{text}'")
    
    # Check if list_apps is disqualified
    valid_intents = set(nlu.intents)
    tag = "list_apps"
    anchors = nlu.intent_anchors.get(tag, [])
    has_anchor = any(a in text for a in anchors)
    print(f"  Intent: {tag}, Anchors: {anchors}, Has Anchor: {has_anchor}")
    
    if not has_anchor:
        print(f"  [SUCCESS] '{tag}' correctly disqualified for '{text}'.")
    else:
        print(f"  [FAIL] '{tag}' NOT disqualified.")

    # 2. Run actual prediction
    pred_tag, conf = nlu.predict(text)
    print(f"  Prediction: {pred_tag} ({conf:.2f})")
    
    if pred_tag == "list_apps":
        print("  [FAIL] Still predicted 'list_apps'!")
    elif pred_tag == "scan_drivers":
        print("  [SUCCESS] Predicted 'scan_drivers'.")
    else:
        print(f"  [INFO] Predicted '{pred_tag}' (Acceptable if not list_apps).")

    # 3. Test "list apps"
    text = "list apps"
    print(f"\nQuery: '{text}'")
    pred_tag, conf = nlu.predict(text)
    print(f"  Prediction: {pred_tag} ({conf:.2f})")
    if pred_tag == "list_apps":
        print("  [SUCCESS] Correctly predicted 'list_apps'.")
    else:
        print("  [FAIL] Did not match 'list_apps'.")

if __name__ == "__main__":
    with open("test_output.txt", "w") as f:
        sys.stdout = f
        test_anchor_logic()
        sys.stdout = sys.__stdout__
    print("Test complete. Output written to test_output.txt")
