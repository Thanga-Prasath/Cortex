import platform
from components.system.custom_utils import run_in_separate_terminal

def get_system_temperature(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Checking system temperature.", blocking=False)
    
    if os_type == 'Linux':
        cmd = "sensors" # requires lm-sensors
        # Auto-install check logic is inside run_in_separate_terminal helper? No, it's in a separate helper.
        # But we need to use get_cmd_with_auto_install if we want that behavior.
        # Importing it here.
        from components.system.custom_utils import get_cmd_with_auto_install
        cmd = get_cmd_with_auto_install("sensors", "lm-sensors")
        run_in_separate_terminal(cmd, "SYSTEM TEMPERATURE", os_type, speaker)
    elif os_type == 'Windows':
        # WMI generic might not show temps without specific drivers.
        # trying a generic wmic command that sometimes works
        cmd = "wmic /namespace:\\\\root\\wmi PATH MSAcpi_ThermalZoneTemperature get CurrentTemperature"
        run_in_separate_terminal(cmd, "SYSTEM TEMPERATURE (x10 Kelvin)", os_type, speaker)
    elif os_type == 'Darwin':
        cmd = "sudo powermetrics --samplers smc |grep -i \"CPU die temperature\""
        run_in_separate_terminal(cmd, "SYSTEM TEMPERATURE", os_type, speaker)
