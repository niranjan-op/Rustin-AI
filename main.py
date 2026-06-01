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


def ensure_ico_format(png_path):
    """Converts a PNG image to ICO format dynamically for Windows."""
    if not os.path.exists(png_path):
        return png_path
        
    ico_path = png_path.rsplit('.', 1)[0] + '.ico'
    if not os.path.exists(ico_path):
        try:
            from PIL import Image
            img = Image.open(png_path)
            img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print(f"Generated {ico_path} from {png_path}")
        except Exception as e:
            print(f"Failed to convert logo to ICO: {e}")
            return png_path # fallback to png
            
    return ico_path


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

    # Determine icon path dynamically
    icon_path = os.path.abspath(os.path.join("public", "logo_dark.png"))
    if sys.platform.startswith("win"):
        icon_path = ensure_ico_format(icon_path)

    # 3. Initialize and boot up the pywebview native GUI window
    webview.create_window(
        title="Rustin AI",
        url=f"http://localhost:{port}",
        width=1000,
        height=750,
        resizable=True,
    )
    
    # Force Windows to use the custom icon for the taskbar instead of python.exe default
    if sys.platform.startswith("win"):
        try:
            import ctypes
            myappid = "rustin.ai.coding.agent.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"Failed to set AppUserModelID: {e}")
    webview.start(private_mode=False, icon=icon_path)
