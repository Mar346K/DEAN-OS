import requests
import sys

class SystemWatchdog:
    def __init__(self):
        # [FIX] Dynamic infrastructure routing
        ollama_host = os.getenv("OLLAMA_HOST", "host.docker.internal")
        oubliette_host = os.getenv("OUBLIETTE_HOST", "127.0.0.1")
        aethelgard_host = os.getenv("AETHELGARD_HOST", "127.0.0.1")

        self.services = {
            "Ollama (Local LLM Engine)": f"http://{ollama_host}:11434/",
            "Oubliette (Docker Sandbox)": f"http://{oubliette_host}:8002/run",
            "Aethelgard (Rust Governor)": f"http://{aethelgard_host}:8003/metrics"
        }

    def run_preflight_check(self):
        print("\n[WATCHDOG] 🐕 Running pre-flight infrastructure check...")
        all_healthy = True

        for name, url in self.services.items():
            try:
                # 1-second timeout. If it's local, it should answer instantly.
                if "run" in url:
                    # Sandbox expects POST requests
                    requests.post(url, json={"code": "print('ok')"}, timeout=1.0)
                else:
                    requests.get(url, timeout=1.0)

                print(f"[WATCHDOG] ✅ {name} is ONLINE.")
            except requests.exceptions.RequestException:
                print(f"[WATCHDOG] ❌ \033[91m{name} is OFFLINE.\033[0m (Connection Refused)")
                all_healthy = False

        if not all_healthy:
            print("\n[WATCHDOG 🛑] Critical infrastructure is missing. Please ensure Ollama is running and you have executed `python daenctl.py up`.")
            print("[WATCHDOG] Halting DEAN-OS Assembly Line to prevent system hangs.\n")
            sys.exit(1)

        print("[WATCHDOG] All systems go. Releasing the swarm...\n")
