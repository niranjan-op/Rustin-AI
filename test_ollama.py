import ollama_manager as m
import urllib.request

print("Port running:", m.is_ollama_running())
print("Discovered port:", m.discover_ollama_port())

# Try connecting to both 127.0.0.1 and localhost
for host in ["127.0.0.1", "localhost"]:
    for port in [11434, 11435]:
        try:
            with urllib.request.urlopen(f"http://{host}:{port}/api/tags", timeout=2) as response:
                print(f"Connection to http://{host}:{port}/api/tags succeeded with status {response.status}")
        except Exception as e:
            print(f"Connection to http://{host}:{port}/api/tags failed: {e}")
