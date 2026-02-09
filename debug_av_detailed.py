import subprocess
import json

def check():
    print("--- DEBUGGING AV DETECTION ---")
    
    # Method 1: PowerShell Get-CimInstance
    print("\n[Method 1] PowerShell Get-CimInstance")
    cmd = "powershell \"Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | Select-Object -Property displayName | ConvertTo-Json\""
    print(f"Running: {cmd}")
    try:
        output = subprocess.check_output(cmd, shell=True).decode().strip()
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

    # Method 2: WMIC
    print("\n[Method 2] WMIC Fallback")
    cmd_wmic = "wmic /namespace:\\\\root\\securitycenter2 path antivirusproduct get displayname /format:list"
    try:
        output = subprocess.check_output(cmd_wmic, shell=True).decode().strip()
        print(f"WMIC Output: '{output}'")
    except Exception as e:
        print(f"WMIC Error: {e}")

if __name__ == "__main__":
    check()
