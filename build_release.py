import os
import urllib.request
import subprocess
import sys

NODE_URL = "https://nodejs.org/dist/v20.14.0/win-x64/node.exe"
NODE_EXE = "node.exe"

def download_node():
    if not os.path.exists(NODE_EXE):
        print(f"Downloading Node.js from {NODE_URL}...")
        urllib.request.urlretrieve(NODE_URL, NODE_EXE)
        print("Download complete.")
    else:
        print(f"{NODE_EXE} already exists.")

def build():
    print("Building executable with PyInstaller...")
    
    # Ensure necessary directories exist to prevent pyinstaller errors
    for d in [".files", "public", ".chainlit"]:
        if not os.path.exists(d):
            os.makedirs(d)
    
    # We create a dummy .env if it doesn't exist
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("")
            
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "Rustin-AI",
        "--onefile",
        "--add-data", f"public;public",
        "--add-data", f".files;.files",
        "--add-data", f".chainlit;.chainlit",
        "--add-data", f"chainlit.md;.",
        "--add-data", f"app.py;.",
        "--add-data", f".env;.",
        "--add-data", f"{NODE_EXE};.",
        "--collect-all", "chainlit",
        "--collect-all", "langchain",
        "--collect-all", "langchain_core",
        "--collect-all", "uvicorn",
        "--collect-all", "websockets",
        "--hidden-import", "app",
        "--hidden-import", "webview",
        "--hidden-import", "sqlalchemy",
        "--hidden-import", "pydantic",
        "--clean",
        "-y", # yes to overwrite
        "main.py"
    ]
    
    # Workaround for mypyc compiled modules (like tomli) failing in PyInstaller
    import site
    import glob
    site_pkgs = site.getsitepackages()
    for sp in site_pkgs:
        for pyd in glob.glob(os.path.join(sp, "*__mypyc*.pyd")):
            mod_name = os.path.basename(pyd).split('.')[0]
            pyinstaller_cmd.extend(["--hidden-import", mod_name])
            
    try:
        subprocess.run(pyinstaller_cmd, check=True)
        print("\n=== Build completed successfully! ===")
        print("You can find the Rustin-AI.exe inside the 'dist' folder.")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")

if __name__ == "__main__":
    download_node()
    build()
