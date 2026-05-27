import re
import string
import subprocess
import threading
import time
import urllib.request

import ollama
import psutil



import psutil
import sys

import urllib.request
import psutil


def try_ollama(port,timeout=1):
    """
    Verify whether Ollama is responding on a port.
    """
    try:
        with urllib.request.urlopen( f"http://127.0.0.1:{port}/api/tags",timeout = timeout) as response:
            if response.status!= 200:
                return False
            else:
                return True
    except Exception:
        return False

def discover_ollama_port():
    """
    Discover the active Ollama port.
    """
    if try_ollama(11434,3):
        return 11434
    ollama_pids = set()
    for proc in psutil.process_iter(["pid","name"]):
        try:
            name  = proc.info["name"]
            if name and "ollama" in name.lower():
                ollama_pids.add(proc.info["pid"])

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not ollama_pids:
        return None
    
    candidate_ports = set()
    try:
        for conn in psutil.net_connections(kind="inet"):

            if (
                conn.pid in ollama_pids
                and conn.status == psutil.CONN_LISTEN
                and conn.laddr
            ):
                candidate_ports.add(conn.laddr.port)

    except psutil.AccessDenied:
        pass

    # Fallback per-process scan
    if not candidate_ports:

        for pid in ollama_pids:
            try:
                proc = psutil.Process(pid)

                for conn in proc.net_connections(kind="inet"):

                    if (
                        conn.status == psutil.CONN_LISTEN
                        and conn.laddr
                    ):
                        candidate_ports.add(conn.laddr.port)

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                AttributeError,
            ):
                continue

    # Validate discovered ports
    for port in sorted(candidate_ports):

        if try_ollama(port):
            return port

    return None
    
    
def _start_server():
    """The internal function that actually runs the subprocess."""
    print("[Ollama] Ollama is offline. Starting local server in the background...")
    try:
        subprocess.Popen(
            ["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # Give it a few seconds to warm up
        time.sleep(3)

        if try_ollama(11434,3):
            print("[Ollama] Ollama server started successfully!")
        else:
            print("[Ollama] Ollama started, but might still be warming up.")

    except FileNotFoundError:
        print(
            "[Ollama] Error: Ollama executable not found. Ensure it is installed and in your PATH."
        )

def is_ollama_running():
    if(try_ollama(11434,3)):
        return 11434
    else:
        port = discover_ollama_port()
        if port:
            if try_ollama(port=port,timeout=3):
                return True
        else:
            _start_server()
            status = try_ollama(11434,3)
            if status: 
                return status
            status = discover_ollama_port()
            return status
            
                
                