from core.nlu import NeuralIntentModel
import time

def test_fuzzy_matching():
    agent = NeuralIntentModel()
    
    # Test cases: (Input, Expected Tag, Expected Confidence > 0.8)
    test_cases = [
        ("clse screen", "console_clear"),       # Typo
        ("create foldr", "file_create_folder"), # Typo
        ("sytem info", "system_info"),          # Typo
        ("what is my ip", "system_ip"),         # Exact match
        ("totally unknown command xyz", None)   # Should fallback to low confidence
    ]

    print(f"{'Input':<30} | {'Predicted':<20} | {'Conf':<6} | {'Result':<10}")
    print("-" * 75)

    passed = 0
    for text, expected_tag in test_cases:
        tag, conf = agent.predict(text)
        
        status = "FAIL"
        if expected_tag is None:
             if conf < 0.5: status = "PASS"
        elif tag == expected_tag and conf == 1.0:
             status = "PASS"
        
        print(f"{text:<30} | {str(tag):<20} | {conf:.2f}   | {status}")
        
        if status == "PASS":
            passed += 1

    print("-" * 75)
    print(f"Passed: {passed}/{len(test_cases)}")

if __name__ == "__main__":
    test_fuzzy_matching()
