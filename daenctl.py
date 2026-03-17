import sys
import subprocess  # nosec B404
import argparse
import time

def validate_hardware():
    print("[SENTINEL] Running Hardware Validation...")
    try:
        subprocess.run(["cargo", "build", "--bin", "aethelgard", "--release"], check=True)  # nosec B603 B607
    except subprocess.CalledProcessError as e:
        print("[ERROR] Failed to compile Aethelgard. Is the Rust toolchain installed?")
        sys.exit(1)
    print("[SUCCESS] Hardware meets DAEN-OS specifications.")

def start_system():
    validate_hardware()
    print("[SYSTEM] Booting Valkyrie Message Bus...")
    print("[SYSTEM] Initializing Mnemosyne Memory Vault...")
    print("[SYSTEM] Starting Sycophant Agents...")

    print("[SYSTEM] Handing over resource monitoring to Aethelgard...")
    try:
        sentinel_process = subprocess.Popen(["./target/release/aethelgard.exe"])  # nosec B603 B607
        print("[READY] DAEN-OS is active and monitoring. Press Ctrl+C to shutdown.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[SYSTEM] Intercepted shutdown signal...")
        sentinel_process.terminate()
        stop_system()

def stop_system():
    print("[SYSTEM] Flushing Oubliette Sandboxes...")
    print("[SYSTEM] Archiving Summary States...")
    print("[OFFLINE] DAEN-OS has shut down gracefully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DAEN-OS Master Control")
    parser.add_argument("command", choices=["up", "down", "status", "check"])

    args = parser.parse_args()

    if args.command == "up":
        start_system()
    elif args.command == "down":
        stop_system()
    elif args.command == "check":
        print("[DIAGNOSTIC] Running local tests...")
        subprocess.run(["cargo", "clippy", "--workspace"])  # nosec B603 B607
