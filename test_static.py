import sys
import os
import subprocess
from unittest.mock import MagicMock, patch

# Ensure we can import from core
sys.path.append(os.getcwd())

def test_static_engine():
    from core.engines.static import StaticCommandEngine
    
    print("Initializing Static Engine...")
    speaker = MagicMock()
    # Mock listener that auto-confirms
    listener = MagicMock()
    listener.listen.return_value = "yes"
    
    engine = StaticCommandEngine(speaker, listener)
    
    if not engine.commands:
        print("[FAIL] Database failed to load.")
        return

    print(f"[SUCCESS] Database loaded with {sum(len(v) for v in engine.commands.values())} entries.")

    test_queries = [
        "check npm version",
        "ping google",
        "list files",
        "shutdown pc", # Should trigger confirm
        "git status"
    ]
    
    print("\n--- Testing Fuzzy Matching ---")
    for query in test_queries:
        print(f"Query: '{query}'")
        key, category, confidence = engine._find_best_match(query)
        if key:
            print(f"  -> Match: {key} (Conf: {confidence:.2f})")
            cmd = engine.commands[category][key]['cmd'].get('windows')
            print(f"  -> Command: {cmd}")
            
    print("\n--- Testing Execution & Safety (Mocked) ---")
    with MagicMock() as mock_popen:
        subprocess.Popen = mock_popen
        
        # Test normal command
        print("\nTest 1: 'git status' (No Confirm)")
        engine.handle_intent(None, "git status")
        if mock_popen.called:
             print("[SUCCESS] Executed immediately.")
        else:
             print("[FAIL] Not executed.")
             
    with MagicMock() as mock_popen:
        subprocess.Popen = mock_popen
        # Test critical command
        print("\nTest 2: 'shutdown pc' (Requires Confirm)")
        engine.handle_intent(None, "shutdown pc")
        
        # Check if speaker asked for confirmation
        speaker.speak.assert_any_call("This is a critical action. Are you sure?")
        
        if mock_popen.called:
             print("[SUCCESS] Executed after confirmation.")
        else:
             print("[FAIL] Not executed.")

    print("\n--- Testing Engine Integration (Mocked) ---")
    with patch('core.speech.Speech'), \
         patch('core.listening.Listener'), \
         patch('core.engines.system.SystemEngine'), \
         patch('core.engines.general.GeneralEngine'), \
         patch('core.engines.file_manager.FileManagerEngine'), \
         patch('core.engines.application.ApplicationEngine'), \
         patch('core.engines.workspace.WorkspaceEngine'), \
         patch('core.engines.automation.AutomationEngine'), \
         patch('core.nlu.NeuralIntentModel'):
        
        with patch.dict(sys.modules, {'core.engines.dynamic': MagicMock()}):
            from core.engine import CortexEngine
            with patch.object(CortexEngine, '_load_user_config', return_value={}):
                engine_instance = CortexEngine(None)
                if hasattr(engine_instance, 'static_engine'):
                    print("[SUCCESS] Static Engine initialized.")
                else:
                    print("[FAIL] Static Engine MISSING.")

if __name__ == "__main__":
    test_static_engine()
