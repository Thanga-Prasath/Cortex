from core.listening import Listener
import time

def verify_fix():
    print("[*] Initializing Listener (this will trigger calibration)...")
    try:
        l = Listener()
        print(f"\n[✓] Calibration Complete.")
        print(f"[✓] Final Threshold: {l.THRESHOLD:.2f}")
        
        if l.THRESHOLD > 4000:
            print("[!] FAIL: Threshold is still suspiciously high (> 4000).")
        elif l.THRESHOLD < 1000:
            print("[✓] SUCCESS: Threshold is in the low range as expected.")
        else:
            print("[?] Threshold is moderate. Check if this is normal for your environment.")
            
        l.terminate()
    except Exception as e:
        print(f"[!] Error during verification: {e}")

if __name__ == "__main__":
    verify_fix()
