import subprocess
import time

import requests

# 1. Start the Node.js server in the background
# print("Starting Node.js server...")
# server_process = subprocess.Popen(
#     ["node", "app.js"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
# )

# 2. Give the server time to boot up
time.sleep(1.5)

url = "http://127.0.0.1:3000"
# Send the exact command you want the server to run
payload = {"command": "whoami", "message": "Hello from this world" * 32}

try:
    # 3. Send the command to the server
    print(f"Sending command '{payload['command']}' to server...")
    response = requests.post(url, json=payload)

    print("\n--- Server Terminal Output ---")
    print(response.text)

except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the server.")

finally:
    # 4. Safely shut down the server
    print("\nShutting down the server...")
    # server_process.terminate()
    # server_process.wait()
    print("Server stopped.")
