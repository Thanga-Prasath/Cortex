import subprocess
import os

def try_close(app_name):
    print(f"--- Trying to close '{app_name}' ---")
    
    # Logic from close_app.py (simplified)
    bin_mapping = {
        "chrome": "google-chrome", 
        "google chrome": "google-chrome",
        "firefox": "firefox",
        "notepad": "notepad",
    }
    
    target_app = bin_mapping.get(app_name.lower(), app_name)
    
    # Simulation of the command
    cmd = f"taskkill /IM {target_app}.exe /F"
    print(f"Command: {cmd}")
    
    # Try actual execution (will fail if app not open, but we see exit code)
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Exit Code: {res.returncode}")
        print(f"Stdout: {res.stdout.strip()}")
        print(f"Stderr: {res.stderr.strip()}")
    except Exception as e:
        print(f"Error: {e}")
        
print("OS: Windows")
try_close("notepad")
try_close("chrome")
try_close("firefox")
try_close("calculator") # likely 'calculator.exe' which is wrong, should be 'calc.exe'
