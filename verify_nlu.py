import time
from core.nlu import NeuralIntentModel

def test_nlu():
    print("Loading Model...")
    start_load = time.time()
    nlu = NeuralIntentModel()
    print(f"Model loaded in {time.time() - start_load:.4f}s")

    test_phrases = ["hello", "hello hello", "time", "what is the time", "exit", "cortex stop"]
    
    print("\n--- Confidence Test ---")
    for phrase in test_phrases:
        start_pred = time.time()
        tag, prob = nlu.predict(phrase)
        duration = time.time() - start_pred
        print(f"Phrase: '{phrase}' -> Tag: {tag}, Confidence: {prob:.4f}, Time: {duration:.6f}s")

if __name__ == "__main__":
    test_nlu()
