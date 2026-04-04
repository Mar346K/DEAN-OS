import sys
import subprocess # nosec B404
import time
import os

# --- CONFIG ---
# explicitly target the uv .venv if it exists, otherwise fallback to system python
venv_python = os.path.abspath(".venv/Scripts/python.exe")
python_exe = venv_python if os.path.exists(venv_python) else sys.executable

SERVICES = {
    # We ONLY run the telemetry locally. Everything else lives in Docker.
    "host_telemetry": [python_exe, "infrastructure/host_telemetry.py"]
}

processes = {}

def start_all():
    print("[SYSTEM] Booting DEAN-OS Infrastructure...")
    print(f"[SYSTEM] Using Python Interpreter: {python_exe}")

    for name, cmd in SERVICES.items():
        print(f"[STARTING] {name} service...")
        try:
            processes[name] = subprocess.Popen(cmd) # nosec B603
        except Exception as e:
            print(f"[ERROR] Failed to start {name}: {e}")

    print("\n[READY] All services online. Running background Forge watcher...")

    try:
        while True:
            # Check for tool requests every 5 seconds
            subprocess.run([python_exe, "infrastructure/quarantine_forge.py"])  # nosec B603 B607
            time.sleep(5)
    except KeyboardInterrupt:
        shutdown()

def shutdown():
    print("\n[SYSTEM] Initiating Graceful Shutdown...")
    for name, proc in processes.items():
        print(f"[STOPPING] {name}...")
        proc.terminate()
    print("[OFFLINE] DEAN-OS is down.")
    sys.exit(0)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["up", "down"])
    args = parser.parse_args()

    if args.command == "up":
        start_all()
