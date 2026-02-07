import shutil
import subprocess
import os
import platform

def check_app(name):
    print(f"--- Checking: '{name}' ---")
    
    # 1. shutil.which
    which_res = shutil.which(name)
    print(f"shutil.which: {which_res}")
    
    # 2. subprocess 'where'
    try:
        where_res = subprocess.check_output(f"where {name}", stderr=subprocess.STDOUT, shell=True).decode().strip()
        print(f"where command: Found\n{where_res}")
    except subprocess.CalledProcessError as e:
        print(f"where command: Not Found (Exit code {e.returncode})")
    except Exception as e:
        print(f"where command: Error {e}")
        
    # 3. os.path.exists
    path_exists = os.path.exists(name)
    print(f"os.path.exists: {path_exists}")

apps_to_test = ["firefox", "explorer", "cmd", "notepad", "main.py", "start.bat", "vr7", "engine"]

print(f"Platform: {platform.system()}")
print(f"CWD: {os.getcwd()}")

for app in apps_to_test:
    check_app(app)
    print("\n")
