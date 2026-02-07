from components.application.app_mapper import AppMapper
import platform

print(f"OS: {platform.system()}")
mapper = AppMapper()

print(f"Total Apps Found: {len(mapper.apps)}")

# Check specific apps
targets = ["whatsapp", "spotify", "calculator", "notepad", "edge", "firefox"]

for t in targets:
    cmd = mapper.search_app(t)
    print(f"App '{t}' -> {cmd}")
