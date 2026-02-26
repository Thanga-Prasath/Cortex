import threading
import time
import platform

def _is_virtual_linux_device(name: str) -> bool:
    """Return True if *name* should be excluded from connect/disconnect monitoring on Linux.
    
    On Linux, ALSA built-in sound cards (e.g. HDA Intel PCH) temporarily vanish
    from PyAudio when TTS or other apps use the device.  Only genuinely external
    devices (USB headsets, Bluetooth speakers) can actually be plugged / unplugged,
    so we only monitor those.
    """
    if platform.system() != 'Linux':
        return False
    upper = name.upper()
    # Keep only devices that are clearly USB or Bluetooth
    if 'USB' in upper or 'BLUETOOTH' in upper or 'BT' in upper:
        return False   # Not virtual — worth monitoring
    return True        # Everything else is excluded on Linux

# Number of consecutive polls a device must be missing before reporting disconnect.
# With a 3-second poll interval this means ~9 seconds of confirmed absence.
_DEBOUNCE_POLLS = 3

class AudioDeviceMonitor(threading.Thread):
    def __init__(self, tts_queue, status_queue, on_change_callback=None):
        super().__init__()
        self.tts_queue = tts_queue
        self.status_queue = status_queue
        self.on_change_callback = on_change_callback
        self.running = True
        self.daemon = True
        
        self.current_inputs = set()
        self.current_outputs = set()
        self.current_default_in = None
        self.current_default_out = None
        
        # Tracks devices that have disappeared but haven't been confirmed gone yet.
        # Key: (device_type, device_name)  Value: consecutive-miss count
        self._pending_removals: dict[tuple[str, str], int] = {}
        
        # Initial snapshot to prevent spamming on startup
        self._poll_devices(initial=True)

    def _poll_devices(self, initial=False):
        import subprocess
        import sys
        import json

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
        if info.get('maxInputChannels', 0) > 0: ins.append(name)
        if info.get('maxOutputChannels', 0) > 0: outs.append(name)
        
    print(json.dumps({'inputs': ins, 'outputs': outs, 'default_in': def_in, 'default_out': def_out}))
    p.terminate()
except Exception as e:
    print(json.dumps({'error': str(e)}))
"""
        try:
            result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=2)
            if result.returncode != 0 or not result.stdout.strip():
                return
                
            data = json.loads(result.stdout.strip())
            if 'error' in data: return
            
            new_inputs = set(d for d in data.get('inputs', []) if not _is_virtual_linux_device(d))
            new_outputs = set(d for d in data.get('outputs', []) if not _is_virtual_linux_device(d))
            new_def_in = data.get('default_in')
            new_def_out = data.get('default_out')
            
            if not initial:
                changed_any = False
                if self._check_diff(self.current_inputs, new_inputs, "Microphone"): changed_any = True
                if self._check_diff(self.current_outputs, new_outputs, "Speaker"): changed_any = True
                
                # Check for default device swaps (e.g. 3.5mm jack rerouting without new PyAudio endpoint)
                if self.current_default_in and new_def_in and self.current_default_in != new_def_in:
                    if new_def_in not in (new_inputs - self.current_inputs):
                        msg = f"Swapped active Microphone to {new_def_in}"
                        print(f"[System] {msg}")
                        changed_any = True
                        
                if self.current_default_out and new_def_out and self.current_default_out != new_def_out:
                    if new_def_out not in (new_outputs - self.current_outputs):
                        msg = f"Swapped active Speaker to {new_def_out}"
                        print(f"[System] {msg}")
                        changed_any = True
                
                if changed_any and self.on_change_callback:
                    self.on_change_callback()
                
            # Keep pending-removal devices in the "current" sets so they
            # don't trigger a false "New connected" when they reappear.
            pending_inputs = {name for (dt, name) in self._pending_removals if dt == "Microphone"}
            pending_outputs = {name for (dt, name) in self._pending_removals if dt == "Speaker"}
            self.current_inputs = new_inputs | pending_inputs
            self.current_outputs = new_outputs | pending_outputs
            self.current_default_in = new_def_in
            self.current_default_out = new_def_out

        except Exception as e:
            print(f"[Audio Monitor] Check error: {e}")

    def _check_diff(self, old_set, new_set, device_type):
        added = new_set - old_set
        removed = old_set - new_set
        changed = False
        
        # --- Handle devices that reappeared (cancel pending removal) ---
        for device in list(self._pending_removals):
            dt, name = device
            if dt == device_type and name in new_set:
                del self._pending_removals[device]
        
        # --- Handle newly added devices ---
        for device in added:
            key = (device_type, device)
            if key in self._pending_removals:
                # Was only transiently gone — silently cancel the pending removal
                del self._pending_removals[key]
            else:
                # Genuinely new device
                msg = f"New {device_type} connected: {device}"
                print(f"[System] {msg}")
                changed = True
                    
        # --- Handle removed devices (debounced) ---
        for device in removed:
            key = (device_type, device)
            count = self._pending_removals.get(key, 0) + 1
            if count >= _DEBOUNCE_POLLS:
                # Confirmed gone — report it
                msg = f"{device_type} disconnected: {device}"
                print(f"[System] {msg}")
                del self._pending_removals[key]
                changed = True
            else:
                # Not confirmed yet — keep it in the "current" set so it isn't
                # reported as added when it comes back next poll
                self._pending_removals[key] = count
                    
        # Notify UI to refresh dropdowns only on confirmed changes
        if changed and self.status_queue:
            self.status_queue.put(("AUDIO_DEVICES_CHANGED", None))
            
        return changed

    def run(self):
        print("[System] Real-time audio hardware monitor started.")
        while self.running:
            time.sleep(3) # Poll every 3 seconds
            self._poll_devices()

    def stop(self):
        self.running = False
