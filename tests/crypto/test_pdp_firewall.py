import valkyrie_crypto
import os

SECRET = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")

def run_firewall_test():
    print("--- INITIATING VALKYRIE PDP PENETRATION TEST ---")

    # 1. Forge a token for the Main Coder agent
    coder_token = valkyrie_crypto.forge_token(agent_name="main-coder-01", role="coder", secret=SECRET)

    # 2. Forge a token for the Sycophant Orchestrator (Admin)
    admin_token = valkyrie_crypto.forge_token(agent_name="sycophant-orchestrator", role="admin", secret=SECRET)

    # TEST A: Coder attempts a legal action
    print("\n[TEST A] Coder requesting 'staging:write' access...")
    if valkyrie_crypto.enforce_scope(coder_token, SECRET, "staging:write"):
        print("✅ Access Granted. Policy acting correctly.")
    else:
        print("❌ Access Denied incorrectly!")

    # TEST B: Coder attempts an illegal action (Privilege Escalation)
    print("\n[TEST B] Coder requesting 'sandbox:execute' access (Privilege Escalation)...")
    if valkyrie_crypto.enforce_scope(coder_token, SECRET, "sandbox:execute"):
        print("❌ CRITICAL VULNERABILITY: Coder bypassed the firewall!")
    else:
        print("✅ Access Denied. Valkyrie intercepted the request.")

    # TEST C: Admin attempting anything
    print("\n[TEST C] Admin requesting 'production:write' access...")
    if valkyrie_crypto.enforce_scope(admin_token, SECRET, "production:write"):
        print("✅ Access Granted via Admin Wildcard.")
    else:
        print("❌ Access Denied incorrectly!")

if __name__ == "__main__":
    run_firewall_test()
