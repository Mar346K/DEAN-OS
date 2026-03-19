import requests
import os
import valkyrie_crypto

class Analyzer:
    def __init__(self, sandbox_url="http://127.0.0.1:8002"):
        self.sandbox_url = sandbox_url
        self.secret = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")

    def evaluate_code(self, test_filename: str) -> dict:
        print(f"[ANALYZER] Dispatching {test_filename} to Oubliette for isolated evaluation...")

        # Forge the Zero-Trust token
        token = valkyrie_crypto.forge_token("analyzer-agent", "admin", self.secret)
        headers = {"Authorization": f"Bearer {token}"}

        # We use a clever wrapper script to trigger pytest programmatically inside the sandbox
        # This prevents us from having to change the Docker entrypoint again.
        run_script = f"""
import pytest
import sys

# Run pytest on the target file
print("--- PYTEST INITIATED ---")
pytest.main(["-v", "{test_filename}"])

# [FIX] Always exit cleanly so Docker hands over the logs instead of throwing an empty ContainerError
sys.exit(0)
"""
        payload = {"code": run_script}

        try:
            # [SECURITY FIX] Added timeout=60 to satisfy Bandit and prevent deadlocks
            resp = requests.post(f"{self.sandbox_url}/run", json=payload, headers=headers, timeout=60)

            # [FIX] Catch hard server crashes before trying to parse JSON
            if resp.status_code != 200:
                print(f"\n[ANALYZER] ❌ SERVER CRASH (HTTP {resp.status_code})")
                return {"status": "error", "type": "server", "logs": resp.text}

            result = resp.json()

            # 1. Catch Docker/Container Level Errors (Timeouts, OOM)
            if "error" in result:
                print("\n[ANALYZER] ❌ LOUD FAILURE: Sandbox Execution Error")
                return {"status": "fail", "type": "loud", "logs": result['details']}

            output = result.get("output", "")

            # 2. Catch Python SyntaxErrors (like our trailing "Note:" text)
            if "SyntaxError" in output or "IndentationError" in output:
                print("\n[ANALYZER] ❌ LOUD FAILURE: Python Syntax/Compilation Error")
                return {"status": "fail", "type": "loud", "logs": output}

            # 3. Catch failed Pytest Assertions
            if "failed" in output.lower() or "ERRORS" in output:
                print("\n[ANALYZER] ⚠️ SILENT FAILURE: Logic/Assertion Errors Detected")
                return {"status": "fail", "type": "silent", "logs": output}

            print("\n[ANALYZER] ✅ PASSED: All tests green. Code is mathematically verified.")
            return {"status": "pass", "logs": output}

        except Exception as e:
            print(f"[ANALYZER ERROR] Sandbox communication failed: {e}")
            return {"status": "error", "logs": str(e)}
