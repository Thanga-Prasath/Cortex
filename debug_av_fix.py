import subprocess
import json

def check():
    print("--- DEBUGGING AV DETECTION (NO PROFILE) ---")
    
    # Method 1: PowerShell Get-CimInstance with -NoProfile
    print("\n[Method 1] PowerShell Get-CimInstance (-NoProfile)")
    # Using specific quoting to avoid shell interpretation issues
    cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | Select-Object -Property displayName | ConvertTo-Json"]
    print(f"Running (list): {cmd}")
    try:
        # shell=False to avoid cmd.exe parsing issues, direct execution
        output = subprocess.check_output(cmd, shell=False).decode().strip()
        print(f"Raw Output: '{output}'")
        if output:
            try:
                if output.startswith('['):
                    data = json.loads(output)
                else:
                    data = [json.loads(output)]
                print(f"JSON Parsed: {data}")
            except Exception as e:
                print(f"JSON Parse Error: {e}")
        else:
            print("Output is empty.")
    except subprocess.CalledProcessError as e:
        print(f"Command Failed: {e}")
    except Exception as e:
        print(f"Execution Error: {e}")

if __name__ == "__main__":
    check()
