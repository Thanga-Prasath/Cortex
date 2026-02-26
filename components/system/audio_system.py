import os
import platform
import subprocess
import shutil

def set_system_audio_device(device_name, is_input):
    """
    Sets the OS-level default audio device cross-platform.
    Returns None on success, or an error string on failure.
    """
    os_type = platform.system()

    if os_type == "Windows":
        return _set_windows_device(device_name, is_input)
    elif os_type == "Darwin":
        return _set_macos_device(device_name, is_input)
    elif os_type == "Linux":
        return _set_linux_device(device_name, is_input)
    else:
        return f"Unsupported OS for system audio switching: {os_type}"

# ─── Windows ──────────────────────────────────────────────────────────────────

def _ensure_windows_dll():
    """Download AudioDeviceCmdlets.dll into data/tools if not present. Returns dll_path or None."""
    import urllib.request, zipfile

    # Anchor to the project root instead of cwd
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    tools_dir = os.path.join(project_root, 'data', 'tools', 'AudioDeviceCmdlets')
    dll_path = os.path.join(tools_dir, 'AudioDeviceCmdlets.dll')

    if os.path.exists(dll_path):
        return dll_path

    os.makedirs(tools_dir, exist_ok=True)
    try:
        url = 'https://www.powershellgallery.com/api/v2/package/AudioDeviceCmdlets/3.1.0.2'
        nupkg_path = os.path.join(tools_dir, 'adc.nupkg')
        urllib.request.urlretrieve(url, nupkg_path)
        with zipfile.ZipFile(nupkg_path, 'r') as z:
            z.extractall(tools_dir)
        try:
            os.remove(nupkg_path)
        except Exception:
            pass
        return dll_path
    except Exception as e:
        return None

def _run_powershell(script, timeout=15):
    """Run a PowerShell script. Returns (stdout, stderr, returncode)."""
    # Prefer native 64-bit PowerShell when running from a 32-bit process
    windir = os.environ.get('WINDIR', r'C:\Windows')
    ps64 = os.path.join(windir, 'sysnative', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
    ps_cmd = ps64 if os.path.exists(ps64) else 'powershell'

    res = subprocess.run(
        [ps_cmd, '-NoProfile', '-NonInteractive', '-Command', script],
        capture_output=True, text=True, timeout=timeout
    )
    return res.stdout, res.stderr, res.returncode

def _set_windows_device(device_name, is_input):
    """Switch system default audio device on Windows using AudioDeviceCmdlets."""
    dll_path = _ensure_windows_dll()
    if not dll_path:
        return "Failed to obtain AudioDeviceCmdlets.dll. Check your internet connection."

    # Determine the device type filter: render = output, capture = input
    device_type_filter = "Capture" if is_input else "Render"

    # List devices via AudioDeviceCmdlets, get JSON so we can match by name
    list_script = f"""
Import-Module "{dll_path}"
Get-AudioDevice -List | Where-Object {{ $_.Type -eq '{device_type_filter}' }} | Select-Object Index, Name | ConvertTo-Json -Compress
"""
    try:
        stdout, stderr, rc = _run_powershell(list_script)
        if rc != 0 or not stdout.strip():
            return f"Failed to list audio devices: {stderr.strip()}"

        import json as _json
        raw = stdout.strip()
        # ConvertTo-Json wraps a single item as object, multiple as array
        parsed = _json.loads(raw)
        if isinstance(parsed, dict):
            parsed = [parsed]

        # Find best matching device by name
        target_index = None
        device_name_lower = device_name.lower()
        for dev in parsed:
            name = dev.get("Name", "") or ""
            if device_name_lower in name.lower() or name.lower() in device_name_lower:
                target_index = dev.get("Index")
                break

        if target_index is None:
            return f"Could not match '{device_name}' to any {device_type_filter} device."

        # Set the device by index
        set_script = f"""
Import-Module "{dll_path}"
Set-AudioDevice -Index {target_index}
"""
        _, stderr2, rc2 = _run_powershell(set_script)
        if rc2 == 0:
            return None  # Success
        return f"Set-AudioDevice failed: {stderr2.strip()}"

    except Exception as e:
        return f"Windows audio switch error: {e}"

# ─── macOS ────────────────────────────────────────────────────────────────────

def _set_macos_device(device_name, is_input):
    """Switch system default audio device on macOS.
    Tries SwitchAudioSource first (brew install switchaudio-osx), then switchaudio-osx.
    """
    device_type_flag = "input" if is_input else "output"

    # Try SwitchAudioSource (modern, more reliable)
    tool = shutil.which("SwitchAudioSource")
    if tool:
        res = subprocess.run(
            [tool, "-t", device_type_flag, "-s", device_name],
            capture_output=True, text=True
        )
        if res.returncode == 0:
            return None
        # If it failed, fall through to list-based matching
        stdout_list = subprocess.run(
            [tool, "-t", device_type_flag, "-a"],
            capture_output=True, text=True
        ).stdout
        best = _fuzzy_match_name(device_name, stdout_list.splitlines())
        if best:
            res2 = subprocess.run([tool, "-t", device_type_flag, "-s", best], capture_output=True, text=True)
            if res2.returncode == 0:
                return None
        return f"SwitchAudioSource failed: {res.stderr.strip()}"

    # Fallback: switchaudio-osx (older name for same tool)
    tool2 = shutil.which("switchaudio-osx")
    if tool2:
        res = subprocess.run(
            [tool2, "-t", device_type_flag, "-s", device_name],
            capture_output=True, text=True
        )
        if res.returncode == 0:
            return None
        return f"switchaudio-osx failed: {res.stderr.strip()}"

    return (
        "No audio switching tool found on macOS. "
        "Please install one via: brew install switchaudio-osx"
    )

# ─── Linux ────────────────────────────────────────────────────────────────────

def _set_linux_device(device_name, is_input):
    """Switch system default audio device on Linux via pactl (PulseAudio / PipeWire)."""
    if not shutil.which("pactl"):
        return "pactl not found. Please install PulseAudio or PipeWire."

    cmd_type = "sources" if is_input else "sinks"
    try:
        res = subprocess.run(
            ["pactl", "list", "short", cmd_type],
            capture_output=True, text=True
        )
        if res.returncode != 0:
            return f"pactl list failed: {res.stderr.strip()}"

        # Each line: index \t name \t module \t sample_spec \t state
        lines = res.stdout.strip().split('\n')
        names = []
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 2:
                names.append(parts[1].strip())

        best = _fuzzy_match_name(device_name, names)
        if not best:
            return f"Could not match '{device_name}' to any pactl {cmd_type[:-1]}."

        set_cmd = "set-default-source" if is_input else "set-default-sink"
        res2 = subprocess.run(["pactl", set_cmd, best], capture_output=True, text=True)
        if res2.returncode == 0:
            return None
        return f"pactl {set_cmd} failed: {res2.stderr.strip()}"

    except Exception as e:
        return f"Linux audio switch error: {e}"

# ─── Shared helpers ───────────────────────────────────────────────────────────

def _fuzzy_match_name(query, candidates):
    """Find the best matching candidate for query using token overlap."""
    if not candidates:
        return None

    query_lower = query.lower()
    query_tokens = query_lower.replace("(", " ").replace(")", " ").split()

    best_match = None
    best_score = 0

    for candidate in candidates:
        cand_lower = candidate.lower()
        # Exact substring match wins immediately
        if query_lower in cand_lower or cand_lower in query_lower:
            return candidate
        score = sum(1 for t in query_tokens if t in cand_lower)
        if score > best_score:
            best_score = score
            best_match = candidate

    return best_match if best_score > 0 else None
