import psutil
import time
import datetime

def get_system_uptime(speaker):
    try:
        boot_time_timestamp = psutil.boot_time()
        bt = datetime.datetime.fromtimestamp(boot_time_timestamp)
        now = datetime.datetime.now()
        
        uptime = now - bt
        
        # Convert timedelta to readable format
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        response_parts = []
        if days > 0:
            response_parts.append(f"{days} days")
        if hours > 0:
            response_parts.append(f"{hours} hours")
        if minutes > 0:
            response_parts.append(f"{minutes} minutes")
            
        if not response_parts:
            response = "less than a minute"
        else:
            response = ", ".join(response_parts)
            
        speaker.speak(f"System has been running for {response}.")
        
    except Exception as e:
        speaker.speak(f"Could not determine system uptime. Error: {e}")
