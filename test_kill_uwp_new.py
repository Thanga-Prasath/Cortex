
import subprocess
import time

def find_kill_uwp(package_fragment):
    print(f"Searching for process with path containing: {package_fragment}")
    
    # PowerShell script to find process by module path
    # We use Get-CimInstance Win32_Process for better path access without admin rights sometimes, 
    # but Get-Process -> MainModule.FileName is standard.
    
    ps_cmd = f"""
    Get-Process | Where-Object {{ $_.MainModule.FileName -like "*{package_fragment}*" }} | Select-Object -ExpandProperty Id
    """
    
    try:
        cmd = ["powershell", "-NoProfile", "-Command", ps_cmd]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        pids = result.stdout.strip().splitlines()
        pids = [p.strip() for p in pids if p.strip()]
        
        if pids:
            print(f"Found PIDs: {pids}")
            for pid in pids:
                print(f"Killing PID {pid}...")
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
        else:
            print("No matching processes found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Ensure calculator is open
    print("Launching Calculator...")
    subprocess.run("start calc", shell=True)
    time.sleep(3)
    
    # AppID: Microsoft.WindowsCalculator_8wekyb3d8bbwe!App
    # Package: Microsoft.WindowsCalculator_8wekyb3d8bbwe
    find_kill_uwp("Microsoft.WindowsCalculator_8wekyb3d8bbwe")
