
import subprocess

def test_get_start_apps():
    print("Testing Get-StartApps...")
    ps_script = "Get-StartApps | ConvertTo-Json"
    try:
        cmd = ["powershell", "-NoProfile", "-Command", ps_script]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        print(f"Output length: {len(result.stdout)}")
        # It returns a list of dicts: { "Name": ..., "AppID": ... }
        import json
        try:
            apps = json.loads(result.stdout)
            # Filter for Calculator and Camera
            targets = ["Calculator", "Camera"]
            for app in apps:
                if app.get("Name") in targets:
                    print(f"Found {app.get('Name')}: {app.get('AppID')}")
        except json.JSONDecodeError:
             print("JSON Decode Error. Raw output start:")
             print(result.stdout[:200])
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_get_start_apps()
