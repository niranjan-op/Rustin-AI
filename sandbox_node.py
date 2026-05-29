import subprocess
import time

import requests


class Node:
    def __init__(self):
        self.url = "http://127.0.0.1:3000"
        self.server_process = None

    # Send the exact command you want the server to run

    def start_server(self):
        print("Starting Node.js server...")
        self.server_process = subprocess.Popen(
            ["node", r"server/app.js"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(2)

    def shutdown(self):
        # 4. Safely shut down the server
        print("\nShutting down the server...")
        self.server_process.terminate()
        self.server_process.wait()
        print("Server stopped.")

    def execute_command(self, command):
        self.start_server()
        payload = {"command": command, "message": "Hello from this world" * 32}

        try:
            # 3. Send the command to the server
            print(f"Sending command '{payload['command']}' to server...")
            response = requests.post(self.url, json=payload)

            print("\n--- Server Terminal Output ---")
            print(response.text)

        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server.")
        self.shutdown()
