import threading
import time

class AudioDeviceMonitor(threading.Thread):
    def __init__(self, tts_queue, status_queue):
        super().__init__()
        self.tts_queue = tts_queue
        self.status_queue = status_queue
        self.running = True
        self.daemon = True
        
        self.current_inputs = set()
        self.current_outputs = set()
        self.current_default_in = None
        self.current_default_out = None
        
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
            
            new_inputs = set(data.get('inputs', []))
            new_outputs = set(data.get('outputs', []))
            new_def_in = data.get('default_in')
            new_def_out = data.get('default_out')
            
            if not initial:
                self._check_diff(self.current_inputs, new_inputs, "Microphone")
                self._check_diff(self.current_outputs, new_outputs, "Speaker")
                
                # Check for default device swaps (e.g. 3.5mm jack rerouting without new PyAudio endpoint)
                if self.current_default_in and new_def_in and self.current_default_in != new_def_in:
                    if new_def_in not in (new_inputs - self.current_inputs):
                        msg = f"Swapped active Microphone to {new_def_in}"
                        print(f"[System] {msg}")
                        if self.tts_queue: self.tts_queue.put(msg)
                        if self.status_queue: self.status_queue.put(("AUDIO_DEVICES_CHANGED", None))
                        
                if self.current_default_out and new_def_out and self.current_default_out != new_def_out:
                    if new_def_out not in (new_outputs - self.current_outputs):
                        msg = f"Swapped active Speaker to {new_def_out}"
                        print(f"[System] {msg}")
                        if self.tts_queue: self.tts_queue.put(msg)
                        if self.status_queue: self.status_queue.put(("AUDIO_DEVICES_CHANGED", None))
                
            self.current_inputs = new_inputs
            self.current_outputs = new_outputs
            self.current_default_in = new_def_in
            self.current_default_out = new_def_out

        except Exception as e:
            print(f"[Audio Monitor] Check error: {e}")

    def _check_diff(self, old_set, new_set, device_type):
        added = new_set - old_set
        removed = old_set - new_set
        
        if added or removed:
            for device in added:
                msg = f"New {device_type} connected: {device}"
                print(f"[System] {msg}")
                if self.tts_queue:
                    self.tts_queue.put(msg)
                    
            for device in removed:
                msg = f"{device_type} disconnected: {device}"
                print(f"[System] {msg}")
                if self.tts_queue:
                    self.tts_queue.put(msg)
                    
            # Notify UI to refresh dropdowns
            if self.status_queue:
                self.status_queue.put(("AUDIO_DEVICES_CHANGED", None))

    def run(self):
        print("[System] Real-time audio hardware monitor started.")
        while self.running:
            time.sleep(3) # Poll every 3 seconds
            self._poll_devices()

    def stop(self):
        self.running = False
