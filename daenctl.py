import sys
import subprocess # nosec B404
import time
import os

# --- CONFIG ---
# sys.executable ensures we use the EXACT same Python environment
# that is currently running this script.
SERVICES = {
    "memory": [sys.executable, "services-python/mnemosyne/app.py"],
    "sandbox": [sys.executable, "services-python/oubliette/app.py"],
    "telemetry": [os.path.abspath("target/debug/aethelgard.exe")]
}

processes = {}

def start_all():
    print("[SYSTEM] Booting DEAN-OS Infrastructure...")

    for name, cmd in SERVICES.items():
        print(f"[STARTING] {name} service...")
        try:
            # We use the absolute path to the Python interpreter
            processes[name] = subprocess.Popen(cmd) # nosec B603
        except Exception as e:
            print(f"[ERROR] Failed to start {name}: {e}")

    print("\n[READY] All services online. Running background Forge watcher...")

    try:
        while True:
            # Check for tool requests every 5 seconds
            subprocess.run([sys.executable, "infrastructure/quarantine_forge.py"])  # nosec B603 B607
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
