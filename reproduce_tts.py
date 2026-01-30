import time
from core.speaking import Speaker

def test_tts_loop():
    print("Initializing Speaker...")
    s = Speaker()
    
    print("Speaking 1...")
    s.speak("This is the first test sentence.")
    
    print("Waiting 2 seconds...")
    time.sleep(2)
    
    print("Speaking 2...")
    s.speak("This is the second test sentence. Can you hear me?")

    print("Waiting 2 seconds...")
    time.sleep(2)

    print("Speaking 3...")
    s.speak("This is the third test sentence. Goodbye.")

if __name__ == "__main__":
    test_tts_loop()
