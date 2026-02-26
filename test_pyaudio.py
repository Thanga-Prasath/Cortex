import pyaudio
import json
import sys

p = pyaudio.PyAudio()
try: api = p.get_default_host_api_info()['index']
except: api = None

ins, outs = [], []
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if api is not None and info.get('hostApi') != api: continue
    name = info.get('name', '')
    if not name or 'Microsoft Sound Mapper' in name: continue
    if info.get('maxInputChannels', 0) > 0: ins.append((i, name))
    if info.get('maxOutputChannels', 0) > 0: outs.append((i, name))

print("INPUTS:")
for idx, name in ins:
    print(f"[{idx}] {name}")

print("\nOUTPUTS:")
for idx, name in outs:
    print(f"[{idx}] {name}")

p.terminate()
