
import subprocess

def check_apps():
    ps_script = """
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Get-StartApps | Select-Object Name, AppID | ConvertTo-Json
    """
    try:
        cmd = ["powershell", "-NoProfile", "-Command", ps_script]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        print(result.stdout)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_apps()
