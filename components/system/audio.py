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
            speaker.speak(f"Error restarting audio: {e}")
