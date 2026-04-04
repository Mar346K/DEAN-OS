import requests
import os
import valkyrie_crypto

class Analyzer:
    def __init__(self, project_id: str = "default"):
        self.project_id = project_id
        oubliette_host = os.getenv("OUBLIETTE_HOST", "127.0.0.1")
        self.sandbox_url = f"http://{oubliette_host}:8002"
        self.secret = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")

    def evaluate_code(self, test_filename: str) -> dict:
        print(f"[ANALYZER] 🔬 Dispatching {test_filename} to Oubliette Sandbox...")

        token = valkyrie_crypto.forge_token("analyzer-agent", "analyzer", self.secret)
        headers = {"Authorization": f"Bearer {token}"}

        # Run pytest inside the sandbox safely
        run_script = f"""
import pytest
import sys
print("--- PYTEST INITIATED ---")
pytest.main(["-v", "{test_filename}"])
sys.exit(0)
"""
        payload = {"code": run_script, "project_id": self.project_id}

        try:
            # 5-SECOND CIRCUIT BREAKER: Prevents infinite loops
            resp = requests.post(f"{self.sandbox_url}/run", json=payload, headers=headers, timeout=5.0)

            if resp.status_code != 200:
                print(f"\n[ANALYZER ❌] SERVER CRASH (HTTP {resp.status_code})")
                return {"status": "error", "type": "server", "logs": resp.text}

            result = resp.json()
            if "error" in result:
                return {"status": "fail", "type": "loud", "logs": result['details']}

            output = result.get("output", "")
            if "SyntaxError" in output or "IndentationError" in output:
                return {"status": "fail", "type": "loud", "logs": output}

            if any(err in output for err in ["ERRORS", "ERROR:", "failed", "collected 0 items", "ModuleNotFoundError"]):
                return {"status": "fail", "type": "silent", "logs": output}

            print("[ANALYZER] ✅ PASSED: Sandbox execution verified.")
            return {"status": "pass", "logs": output}

        except requests.exceptions.Timeout:
            print("\n[ANALYZER 🛑] CIRCUIT BREAKER TRIPPED: Infinite loop detected.")
            return {"status": "fail", "type": "loud", "logs": "CRITICAL ERROR: Execution timed out after 5 seconds. Infinite loop detected."}
        except Exception as e:
            return {"status": "error", "logs": str(e)}
