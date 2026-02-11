import psutil

def check_battery_status(speaker):
    try:
        battery = psutil.sensors_battery()
        
        if battery is None:
            speaker.speak("This system does not appear to have a battery.")
            return

        percent = int(battery.percent)
        plugged = battery.power_plugged
        
        status = "charging" if plugged else "discharging"
        
        if plugged:
            if percent == 100:
                 speaker.speak(f"Battery is fully charged at 100%.")
            else:
                 speaker.speak(f"Battery is at {percent}% and charging.")
        else:
            # Estimate time left if available
            if battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                hours, remainder = divmod(battery.secsleft, 3600)
                minutes, _ = divmod(remainder, 60)
                time_left_str = f"About {hours} hours and {minutes} minutes remaining."
                speaker.speak(f"Battery is at {percent}%. {time_left_str}")
            else:
                speaker.speak(f"Battery is at {percent}%.")
                
    except Exception as e:
        speaker.speak(f"Could not check battery status. Error: {e}")
