
import subprocess
import time

def test_uwp_pid():
    app_id = "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App"
    print(f"Attempting to launch {app_id} via PowerShell...")
    
    ps_cmd = f"Start-Process -FilePath 'shell:AppsFolder\\{app_id}' -PassThru | Select-Object -ExpandProperty Id"
    
    try:
        cmd = ["powershell", "-NoProfile", "-Command", ps_cmd]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Result Return Code: {result.returncode}")
        print(f"Result Stdout: '{result.stdout.strip()}'")
        print(f"Result Stderr: '{result.stderr.strip()}'")
        
        pid_str = result.stdout.strip()
        if pid_str.isdigit():
            pid = int(pid_str)
            print(f"Captured PID: {pid}")
            
            print("Waiting 3 seconds...")
            time.sleep(3)
            
            print(f"Attempting to kill PID {pid}...")
            kill_cmd = ["taskkill", "/F", "/PID", str(pid)]
            kill_res = subprocess.run(kill_cmd, capture_output=True, text=True)
            print(f"Kill Output: {kill_res.stdout}")
            print(f"Kill Error: {kill_res.stderr}")
        else:
            print("Failed to capture valid PID.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_uwp_pid()
