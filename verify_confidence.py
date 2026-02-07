import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to sys.path
sys.path.append(os.getcwd())

from core.engine import CortexEngine

def test_confidence_logic():
    # Mock Speaker and Listener
    mock_speaker = MagicMock()
    mock_listener = MagicMock()
    
    with patch('core.engine.Speaker', return_value=mock_speaker), \
         patch('core.engine.Listener', return_value=mock_listener), \
         patch('core.engine.NeuralIntentModel') as mock_nlu_class:
        
        mock_nlu = mock_nlu_class.return_value
        engine = CortexEngine()
        
        # Test Case 1: High Confidence (0.90) - Should execute immediately
        print("\n--- Test Case 1: High Confidence ---")
        mock_listener.listen.side_effect = ["check ip", "exit"] # 1st call for command, 2nd for exit
        mock_nlu.predict.side_effect = [("system_ip", 0.90), ("exit", 1.0)]
        
        # We need to stop the loop, so we'll use a side effect that raises an exception or we mock handle_intent to return True and then 'exit'
        engine.system_engine.handle_intent = MagicMock(return_value=True)
        
        try:
            engine.run()
        except StopIteration:
            pass
            
        print("High confidence test finished (Check logs for execution)")

        # Test Case 2: Medium Confidence (0.75) + Positive Response - Should execute
        print("\n--- Test Case 2: Medium Confidence + Yes ---")
        mock_listener.listen.side_effect = ["check ip", "yes", "exit"]
        mock_nlu.predict.side_effect = [("system_ip", 0.75), ("exit", 1.0)]
        
        engine.run()
        # Verify speaker asked "Did you say Check IP address?"
        mock_speaker.speak.assert_any_call("Did you say Check IP address?")
        print("Medium confidence + Yes test finished")

        # Test Case 4: Parametric Confirmation (app_close)
        print("\n--- Test Case 4: Parametric Confirmation ---")
        mock_listener.listen.side_effect = ["close firefox", "yes", "exit"]
        mock_nlu.predict.side_effect = [("app_close", 0.75), ("exit", 1.0)]
        
        engine.run()
        mock_speaker.speak.assert_any_call("Did you say Close Firefox?")
        print("Parametric confirmation test finished (Verified 'Close Firefox')")

if __name__ == "__main__":
    test_confidence_logic()
