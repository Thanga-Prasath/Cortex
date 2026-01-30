import time
from core.speaking import Speaker
from core.listening import Listener

def test_conflict():
    print("Initializing Speaker and Listener...")
    s = Speaker()
    l = Listener()
    
    print("\n--- TEST 1 ---")
    s.speak("Greeting. This is test one.")
    
    print("\n--- LISTENING SIMULATION ---")
    print("Pretending to listen (opening stream)...")
    try:
        # Just open and close stream briefly to simulate usage
        with l.p.open(format=l.FORMAT, channels=l.CHANNELS, rate=l.RATE, input=True, frames_per_buffer=l.CHUNK) as stream:
             print("Stream opened... reading briefly.")
             for _ in range(10):
                 stream.read(l.CHUNK)
    except Exception as e:
        print(f"Error during listen sim: {e}")
        
    print("\n--- TEST 2 ---")
    s.speak("Response. This is test two.")
    
    # Try again
    print("\n--- LISTENING SIMULATION 2 ---")
    try:
        with l.p.open(format=l.FORMAT, channels=l.CHANNELS, rate=l.RATE, input=True, frames_per_buffer=l.CHUNK) as stream:
             print("Stream opened 2... reading briefly.")
             for _ in range(10):
                 stream.read(l.CHUNK)
    except Exception as e:
        print(f"Error during listen sim 2: {e}")

    print("\n--- TEST 3 ---")
    s.speak("Goodbye. This is test three.")

if __name__ == "__main__":
    test_conflict()
