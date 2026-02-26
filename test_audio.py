import os
import sys

# Ensure correct path
project_root = r"c:\New folder\Sunday-final-year"
sys.path.append(project_root)

# Since components.system.audio_system does imports, let's CD to project root
os.chdir(project_root)

from components.system.audio_system import _ensure_windows_dll, _run_powershell
import json

dll_path = _ensure_windows_dll()
print(f"DLL Path: {dll_path}")
if not dll_path:
    print("DLL missing!")
    sys.exit(1)

list_script = f"""
Import-Module "{dll_path}"
Get-AudioDevice -List | Select-Object Index, Name, Type | ConvertTo-Json -Compress
"""
stdout, stderr, rc = _run_powershell(list_script)
print(f"RC: {rc}")
print(f"STDERR: {stderr}")
print(f"STDOUT: {stdout[:200]}...")

try:
    parsed = json.loads(stdout.strip())
    if isinstance(parsed, dict):
        parsed = [parsed]
    for d in parsed:
        print(d)
except Exception as e:
    print(f"JSON Parse Error: {e}")
