import os
import requests
import valkyrie_crypto

SECRET = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")
# [FIX] Use an identity/role that actually has the sandbox:execute scope
token = valkyrie_crypto.forge_token("test-mount", "analyzer", SECRET)
headers = {"Authorization": f"Bearer " + token}

print("[TEST] Sending execution request to Oubliette...")

payload = {"entrypoint": "test_mount.py"}

try:
    resp = requests.post("http://127.0.0.1:8002/run", json=payload, headers=headers)
    print("\n[RESPONSE]:\n", resp.json())
except Exception as e:
    print(f"[FAILED] Could not reach Sandbox: {e}")
