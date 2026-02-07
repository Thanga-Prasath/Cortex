from core.speaking import Speaker
import time
import os
import sys
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # Ensure we can import core
    sys.path.append(os.getcwd())

    print("--- Testing Piper TTS on Windows ---")
    try:
        s = Speaker()
        print(f"[*] OS Type: {s.os_type}")
        print(f"[*] Piper Available: {s.piper_available}")
        
        if s.piper_available:
            print(f"[*] Piper Path: {s.piper_path}")
            print("[*] Speaking...")
            s.speak("Hello! This is the new human voice on Windows. I hope you like it.")
            
            # Keep alive for a bit
            for i in range(5):
                 time.sleep(1)
                 print(f"Waiting... {i+1}")
                 
            s.terminate()
            print("[*] Done.")
        else:
            print("[!] Piper not detected!")
            print(f"[!] Expected Path: {s.piper_path}")
            
    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()
