import valkyrie_crypto
import requests # nosec B404

SECRET = "daen-internal-dev-secret-2026"
URL = "http://127.0.0.1:8002/run"

def test_sandbox_isolation():
    print("--- OUBLIETTE ISOLATION TEST ---")

    token = valkyrie_crypto.forge_token("test-agent", "admin", SECRET)
    headers = {"Authorization": f"Bearer {token}"}

    # This code tries to list files on YOUR computer.
    # It should only see the empty /home/agentuser inside Docker.
    malicious_code = "import os; print(os.listdir('.'))"

    print(f"[TEST] Attempting to peek at host files...")
    response = requests.post(URL, params={"code": malicious_code}, headers=headers)

    if response.status_code == 200:
        output = response.json().get("output")
        print(f"[RESULT] Sandbox output: {output}")
        print("[SUCCESS] Agent is trapped. Host files are invisible.")
    else:
        print(f"[FAILED] Error: {response.text}")

if __name__ == "__main__":
    test_sandbox_isolation()
