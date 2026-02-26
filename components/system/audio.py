import platform
import subprocess
import time

def restart_audio_service(speaker):
    os_type = platform.system()
    
    if os_type == 'Windows':
        speaker.speak("Restarting Windows Audio services. This may take a moment.")
        try:
            # Requires Admin privileges usually.
            # We try to stop and start Audiosrv and AudioEndpointBuilder
            
            # Stop
            subprocess.run(["net", "stop", "Audiosrv", "/y"], capture_output=True)
            subprocess.run(["net", "stop", "AudioEndpointBuilder", "/y"], capture_output=True)
            
            time.sleep(1)
            
            # Start
            subprocess.run(["net", "start", "AudioEndpointBuilder"], capture_output=True)
            subprocess.run(["net", "start", "Audiosrv"], capture_output=True)
            
            speaker.speak("Audio services restarted.")
        except Exception as e:
            speaker.speak(f"Failed to restart audio services. Ensure you have administrator rights. Error: {e}")

    elif os_type == 'Darwin': # macOS
        speaker.speak("Restarting Core Audio.")
        try:
            subprocess.run(["sudo", "killall", "coreaudiod"], capture_output=True)
            speaker.speak("Core Audio restarted.")
        except Exception as e:
            speaker.speak(f"Failed to restart Core Audio: {e}")

    elif os_type == 'Linux':
        speaker.speak("Restarting Linux Audio.")
        try:
             # Try PulseAudio first
             # check=True will raise CalledProcessError if it returns non-zero (i.e. fails)
             try:
                 subprocess.run(["pulseaudio", "-k"], check=True, capture_output=True)
                 subprocess.run(["pulseaudio", "--start"], check=True, capture_output=True)
                 speaker.speak("PulseAudio restarted.")
                 return
             except (FileNotFoundError, subprocess.CalledProcessError):
                 pass # Fall through to PipeWire

             # Try PipeWire
             try:
                 subprocess.run(["systemctl", "--user", "restart", "pipewire"], check=True, capture_output=True)
                 speaker.speak("PipeWire restarted.")
                 return
             except (FileNotFoundError, subprocess.CalledProcessError):
                 pass
                 
             speaker.speak("Could not restart PulseAudio or PipeWire.")
             
        except Exception as e:
            if "permission denied" in str(e).lower() or "not allowed" in str(e).lower():
                speaker.speak(f"Error restarting audio: Permission denied. Please run the permission repair script.")
            else:
                speaker.speak(f"Error restarting audio: {e}")

def _toggle_device(speaker, device_type="input", system_wide=False):
    """Toggles between System Default and the first found non-default PyAudio device."""
    import os
    import json
    try:
        import pyaudio
        from core.alsa_error import no_alsa_error
    except ImportError:
        speaker.speak("PyAudio is not installed.")
        return

    config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')
    data = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
        except: pass
        
    config_key = f"{device_type}_device_name"
    
    # Connect to PyAudio via subprocess to get a fresh, un-cached device graph
    import subprocess
    import sys
    
    script = """
import pyaudio, json, sys, os
sys.stderr = open(os.devnull, 'w')
try:
    p = pyaudio.PyAudio()
    try: api = p.get_default_host_api_info()['index']
    except: api = None
    
    try: def_in = p.get_default_input_device_info().get('name')
    except: def_in = None
    
    try: def_out = p.get_default_output_device_info().get('name')
    except: def_out = None
    
    ins, outs = [], []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if api is not None and info.get('hostApi') != api: continue
        name = info.get('name', '')
        if not name or 'Microsoft Sound Mapper' in name: continue
        if info.get('maxInputChannels', 0) > 0 and name not in ins: ins.append(name)
        if info.get('maxOutputChannels', 0) > 0 and name not in outs: outs.append(name)
        
    print(json.dumps({'inputs': ins, 'outputs': outs, 'default_in': def_in, 'default_out': def_out}))
    p.terminate()
except Exception as e:
    print(json.dumps({'error': str(e)}))
"""
    available_devices = []
    default_device_name = None
    
    try:
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=2)
        if result.returncode == 0 and result.stdout.strip():
            # Robust JSON parsing to ignore any ALSA/PyAudio warnings intermixed in stdout
            import re
            match = re.search(r'\{.*\}', result.stdout.strip(), re.DOTALL)
            if match:
                scanned_data = json.loads(match.group(0))
                if 'error' not in scanned_data:
                    if device_type == "input":
                        available_devices = scanned_data.get('inputs', [])
                        default_device_name = scanned_data.get('default_in')
                    else:
                        available_devices = scanned_data.get('outputs', [])
                        default_device_name = scanned_data.get('default_out')
    except Exception as e:
        print(f"[Audio Toggle] Error identifying devices: {e}")
            
    if not available_devices:
        speaker.speak(f"No {device_type} devices found.")
        return
    elif len(available_devices) == 1:
        speaker.speak(f"Only one {device_type} device is available. Cannot switch.")
        return
        
    # Toggle Logic:
    if system_wide:
        current_device = default_device_name
    else:
        current_device = data.get(config_key)
        if current_device is None:
            current_device = default_device_name
        
    if current_device in available_devices:
        current_idx = available_devices.index(current_device)
        next_idx = (current_idx + 1) % len(available_devices)
        new_device = available_devices[next_idx]
    else:
        new_device = available_devices[0]

    if system_wide:
        from components.system.audio_system import set_system_audio_device
        err = set_system_audio_device(new_device, device_type == "input")
        if err:
            speaker.speak(f"Failed to change system default: {err}")
        else:
            word = "microphone" if device_type == "input" else "speaker"
            speaker.speak(f"System {word} changed to {new_device}.")
    else:
        msg = f"Switched {device_type} to {new_device}."
        data[config_key] = new_device
        try:
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=4)
            speaker.speak(msg)
        except Exception as e:
            speaker.speak(f"Failed to save settings: {e}")

def switch_system_microphone(speaker):
    _toggle_device(speaker, "input", True)

def switch_system_speaker(speaker):
    _toggle_device(speaker, "output", True)
