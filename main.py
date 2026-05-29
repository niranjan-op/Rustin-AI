import os
import socket
import sys
import threading
import time

# Reconfigure stdout/stderr to support UTF-8 (emojis/unicode characters) on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

import webview
from chainlit.cli import run_chainlit


def get_free_port(preferred_port=8000):
    """Finds an available local port dynamically, prioritizing the preferred port."""
    # Check if the preferred port is available
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("127.0.0.1", preferred_port))
        s.close()
        return preferred_port
    except socket.error:
        pass

    # If preferred port is in use, find any other free port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def start_chainlit(target_file, port):
    """Runs the Chainlit server in a background thread."""
    from chainlit.config import config

    # Configure environment variables that run_chainlit reads
    os.environ["CHAINLIT_PORT"] = str(port)
    os.environ["CHAINLIT_HOST"] = "127.0.0.1"

    # Prevent Chainlit from opening a new browser tab automatically
    config.run.headless = True
    config.run.watch = False

    run_chainlit(target_file)


if __name__ == "__main__":
    # Define your Chainlit script filename
    chainlit_script = "app.py"
    port = get_free_port()

    # 1. Spin up Chainlit in the background
    server_thread = threading.Thread(
        target=start_chainlit, args=(chainlit_script, port), daemon=True
    )
    server_thread.start()

    # 2. Give the Chainlit server a brief moment to spin up and bind
    time.sleep(10)

    # 3. Initialize and boot up the pywebview native GUI window
    webview.create_window(
        title="My Chat AI App",
        url=f"http://localhost:{port}",
        width=1000,
        height=750,
        resizable=True,
    )
    webview.start(private_mode=False)
