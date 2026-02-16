import pyaudio
import numpy as np
import time

def diagnose_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()
    
    print(f"[*] Opening stream (Rate: {RATE}, Chunk: {CHUNK})...")
    try:
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    except Exception as e:
        print(f"[!] Could not open stream: {e}")
        return
    
    print("[*] Reading 50 chunks of audio in silence (roughly 3 seconds)...")
    
    all_means = []
    all_rms = []
    
    for i in range(50):
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            
            mean_val = np.mean(samples)
            rms_val = np.sqrt(np.mean(samples**2))
            
            all_means.append(mean_val)
            all_rms.append(rms_val)
            
            if i % 10 == 0:
                print(f"Chunk {i:02d}: Mean={mean_val:8.2f}, RMS={rms_val:8.2f}, Min={np.min(samples):8.0f}, Max={np.max(samples):8.0f}")
        except Exception as e:
            print(f"[!] Error reading chunk {i}: {e}")
            break

    stream.stop_stream()
    stream.close()
    p.terminate()
    
    print("\n--- Summary ---")
    print(f"Average Mean (DC Offset): {np.mean(all_means):.2f}")
    print(f"Average RMS (Noise Floor): {np.mean(all_rms):.2f}")
    print(f"RMS Variance: {np.var(all_rms):.2f}")
    
    if abs(np.mean(all_means)) > 50:
        print("[!] DC Offset detected. This will skew noise calibration.")
        print("    Recommendation: Subtract the mean from samples before calculating RMS.")
    
    if np.mean(all_rms) > 2000:
        print("[!] Noise floor is very high. Possible reasons:")
        print("    1. Hardware gain is set too high (check OS settings/alsamixer).")
        print("    2. Software AGC (Auto Gain Control) is boosting silence.")
        print("    3. Driver-level noise that settles after the first use.")

if __name__ == "__main__":
    diagnose_audio()
