import unittest
from unittest.mock import MagicMock
from core.engines.dynamic import DynamicCommandEngine
import platform

class TestDynamicEngine(unittest.TestCase):
    def setUp(self):
        self.speaker = MagicMock()
        self.engine = DynamicCommandEngine(self.speaker)
        
    def test_load_mappings(self):
        # We expect at least the 3 commands we added to system.json
        print(f"Loaded mappings: {list(self.engine.intent_mappings.keys())}")
        self.assertIn('system_ip', self.engine.intent_mappings)
        self.assertIn('check_ports', self.engine.intent_mappings)
        
    def test_handle_system_ip(self):
        # Test handling of the system_ip tag
        result = self.engine.handle_intent('system_ip')
        self.assertTrue(result)
        
        # Verify speaker was called (since we defined speak_before)
        self.speaker.speak.assert_called()
        args = self.speaker.speak.call_args[0][0]
        print(f"Speaker called with: {args}")
        self.assertIn("Checking", args)

if __name__ == '__main__':
    unittest.main()
