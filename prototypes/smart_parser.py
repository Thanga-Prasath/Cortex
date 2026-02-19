import platform

class SmartCommandParser:
    def __init__(self):
        self.os_type = platform.system().lower()
        if self.os_type == "darwin": self.os_type = "macos"
        
        # 1. Action Grammar
        self.actions = {
            "list": ["list", "show", "display", "what are", "ls"],
            "remove": ["remove", "delete", "clear", "erase", "rm"],
            "create": ["create", "make", "generate", "new", "mkdir", "touch"],
            "check": ["check", "monitor", "status", "verify", "how is"]
        }
        
        # 2. Object Grammar
        self.objects = {
            "file": ["file", "files", "document", "docs"],
            "folder": ["folder", "directory", "dir", "path"],
            "process": ["process", "program", "app", "task"],
            "network": ["network", "internet", "wifi", "connection", "ip", "port"],
            "system": ["system", "computer", "pc", "machine", "cpu", "ram", "memory", "disk"]
        }
        
        # 3. Command Templates (The "Brain")
        self.templates = {
            "windows": {
                "list_file": "dir /b",
                "list_folder": "dir /ad /b",
                "remove_file": "del /q {}",
                "remove_folder": "rmdir /s /q {}",
                "create_folder": "mkdir {}",
                "create_file": "type nul > {}",
                "check_process": "tasklist",
                "kill_process": "taskkill /f /im {}",
                "check_ip": "ipconfig",
                "check_ram": "systeminfo | findstr /C:\"Total Physical Memory\"",
                "check_disk": "wmic logicaldisk get size,freespace,caption"
            },
            "linux": {
                "list_file": "ls -la",
                "list_folder": "ls -d */",
                "remove_file": "rm {}",
                "remove_folder": "rm -rf {}",
                "create_folder": "mkdir -p {}",
                "create_file": "touch {}",
                "check_process": "ps aux",
                "kill_process": "pkill -f {}",
                "check_ip": "hostname -I",
                "check_ram": "free -h",
                "check_disk": "df -h"
            }
        }
        # Fallback
        if self.os_type not in self.templates:
            self.templates[self.os_type] = self.templates["linux"]

    def parse(self, text):
        text = text.lower()
        
        # 1. Identifiy Action
        detected_action = None
        for action, keywords in self.actions.items():
            if any(k in text for k in keywords):
                detected_action = action
                break
        
        # 2. Identify Object
        detected_object = None
        for obj, keywords in self.objects.items():
            if any(k in text for k in keywords):
                detected_object = obj
                break
                
        # 3. Heuristic: "IP" is a special object
        if "ip" in text: 
            detected_action = "check"
            detected_object = "ip"
        elif "ram" in text or "memory" in text:
            detected_action = "check"
            detected_object = "ram"

        if not detected_action or not detected_object:
            return None, "I couldn't understand the action or object."
            
        # 4. Construct Key
        key = f"{detected_action}_{detected_object}"
        print(f"[Debug] Key: {key}")
        
        template = self.templates[self.os_type].get(key)
        
        if not template:
            return None, f"I don't know how to {detected_action} {detected_object} on {self.os_type} yet."
            
        # 5. Entity Extraction (Simple Suffix)
        # "create folder my_project" -> returns "my_project"
        entity = ""
        action_keywords = self.actions.get(detected_action, [])
        object_keywords = self.objects.get(detected_object, [])
        
        # Remove trigger words to find entity
        words = text.split()
        filtered_words = [w for w in words if w not in action_keywords and w not in object_keywords and w not in ["the", "a", "an", "all", "my"]]
        
        if filtered_words:
            entity = " ".join(filtered_words)
            
        if "{}" in template:
            if entity:
                return template.format(entity), None
            else:
                return None, f"What {detected_object} should I {detected_action}?"
        
        return template, None

# Test
if __name__ == "__main__":
    parser = SmartCommandParser()
    cmds = [
        "what is my ip",
        "show running processes",
        "create folder projects",
        "check system memory",
        "list all files"
    ]
    
    print("-" * 30)
    for txt in cmds:
        cmd, err = parser.parse(txt)
        if cmd:
            print(f"'{txt}' -> `{cmd}`")
        else:
            print(f"'{txt}' -> Error: {err}")
