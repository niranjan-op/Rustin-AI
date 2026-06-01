import subprocess
import time
from pathlib import Path

import requests


class Node:
    def __init__(self):
        self.url = "http://127.0.0.1:3000"
        self.server_process = None
        self.project_path = None

    # Send the exact command you want the server to run

    def start_server(self):
        if self.server_process is not None:
            if self.server_process.poll() is None:
                # It's actually running and healthy
                return
            else:
                self.server_process = None

        # Safely attempt to kill any zombie node server on port 3000
        try:
            requests.post(self.url + "/shutdown", timeout=1)
        except Exception:
            pass

        print("Starting Node.js server...")

        # Absolute path to the app.js script
        script_path = str(Path(__file__).parent / "public" / "server" / "app.js")

        # Use self.project_path if available, otherwise fallback to current directory
        cwd = (
            self.project_path
            if hasattr(self, "project_path") and self.project_path
            else None
        )

        self.server_process = subprocess.Popen(
            ["node", script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            cwd=cwd,
        )
        time.sleep(2)

    def shutdown(self):
        # 4. Safely shut down the server
        try:
            requests.post(self.url + "/shutdown", timeout=1)
        except Exception:
            pass
            
        if self.server_process:
            print("\nShutting down the server...")
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None
            print("Server stopped.")

    def execute_command(self, command):
        # Guarantee the server is running before attempting to send commands
        self.start_server()

        payload = {
            "command": command,
            "projectPath": self.project_path,
            "message": "Hello from this world" * 32,
        }

        try:
            # 3. Send the command to the server
            print(f"Sending command '{payload['command']}' to server...")
            response = requests.post(self.url, json=payload, timeout=10)

            print("\n--- Server Terminal Output ---")
            print(response.text)
            return response.text

        except requests.exceptions.Timeout:
            print("Error: The command took too long to respond and timed out.")
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server.")

        return None

    def not_starting_server(self, command):
        print(f"Project_path:{self.project_path}")
        payload = {
            "command": command,
            "projectPath": self.project_path,
            "message": "Hello from this world" * 32,
        }

        try:
            # 3. Send the command to the server
            print(f"Sending command '{payload['command']}' to server...")
            response = requests.post(self.url, json=payload)

            print("\n--- Server Terminal Output ---")
            print(response.text)
            return response.text

        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server.")

        return None

    def create_file_to_wkng_dir(self, path, content, name):
        try:
            target = Path(path) / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as file:
                file.write(content)
            print("File Created Successfully")
            return True
        except Exception as e:
            print(f"Error creating file: {e}")
            return str(e)

    def append_file_to_wkng_dir(self, path, content, name):
        try:
            target = Path(path) / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "a", encoding="utf-8") as file:
                file.write(content)
            print("File Appended Successfully")
            return True
        except Exception as e:
            print(f"Error appending file: {e}")
            return str(e)


import atexit

node_instance = Node()
atexit.register(node_instance.shutdown)
