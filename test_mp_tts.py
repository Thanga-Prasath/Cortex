import multiprocessing
import pyttsx3
import time

def run_tts_process(text):
    """
    Run TTS in a separate process to avoid event loop conflicts.
    """
    try:
        engine = pyttsx3.init()
        # Configure voice (simplified for test)
        voices = engine.getProperty('voices')
        for voice in voices:
            if 'zira' in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        engine.setProperty('rate', 175)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS Process Error: {e}")

def test_mp():
    print("Testing Multiprocessing TTS...")
    
    p1 = multiprocessing.Process(target=run_tts_process, args=("Hello from process 1",))
    p1.start()
    p1.join()
    
    print("Process 1 done. Waiting...")
    time.sleep(1)
    
    p2 = multiprocessing.Process(target=run_tts_process, args=("Hello from process 2",))
    p2.start()
    p2.join()
    
    print("Process 2 done.")

if __name__ == "__main__":
    test_mp()
