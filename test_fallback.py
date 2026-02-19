import sys
import os
# Mocking parts of the system for test
from unittest.mock import MagicMock, patch

# Ensure we can import from core
sys.path.append(os.getcwd())

def test_fallback_logic():
    speaker = MagicMock()
    status_queue = MagicMock()
    
    # We need to mock the Brain because we don't want to load 350MB in a unit test
    with patch('core.engines.nlp.brain.CommandBrain.generate_command') as mock_gen:
        mock_gen.return_value = "wmic path win32_battery get fullchargercount"
        
        from core.engine import CortexEngine
        engine = CortexEngine(status_queue)
        
        # Test Case 1: Battery Cycle (High confidence but specific keyword)
        # tag='check_battery', confidence=1.0, command='what is my battery cycle'
        print("Testing Case 1: 'what is my battery cycle' (High confidence intent)")
        # SystemEngine should return False for 'cycle'
        res = engine.execute_intent('check_battery', 'what is my battery cycle')
        print(f"Result for Case 1: {res}")
        if res:
            print("[SUCCESS] Falls through and executes via Brain.")
            mock_gen.assert_called()
        else:
            print("[FAIL] Did not execute via Brain.")

        # Test Case 2: Unrecognized Command (Low confidence)
        mock_gen.reset_mock()
        print("\nTesting Case 2: 'how many times i charge' (Low confidence/Unknown)")
        # We simulate the loop fallback
        # In the loop, if res is False, it calls dynamic_engine.handle_intent(None, command)
        res = engine.dynamic_engine.handle_intent(None, 'how many times i charge')
        print(f"Result for Case 2: {res}")
        if res:
             print("[SUCCESS] Handled via Brain fallback.")
             mock_gen.assert_called()
        else:
             print("[FAIL] Brain fallback failed.")

if __name__ == "__main__":
    test_fallback_logic()
