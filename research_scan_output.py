import subprocess
import threading

def read_stream(stream):
    while True:
        line = stream.readline()
        if not line:
            break
        print(f"[OUTPUT]: {line.decode('utf-8', errors='ignore').strip()}")

if __name__ == "__main__":
    print("--- Checking MpCmdRun Output ---")
    defender_path = r"C:\Program Files\Windows Defender\MpCmdRun.exe"
    
    # Try running a scan and capturing output
    # Using 'scan' command
    cmd = [defender_path, "-Scan", "-ScanType", "1"]
    
    print(f"Running: {cmd}")
    
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    
    read_stream(process.stdout)
    process.wait()
    print("--- Done ---")
