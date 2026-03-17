import valkyrie_crypto
import requests # uv pip install requests if needed

SECRET = "daen-internal-dev-secret-2026"
URL = "http://127.0.0.1:8001/search"

def query_librarian(question: str):
    print(f"[TEST] Asking Librarian: '{question}'")

    # 1. Forge a valid token using our Rust layer
    token = valkyrie_crypto.forge_token("test-client", "admin", SECRET)
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Query the Mnemosyne service
    response = requests.post(URL, params={"query": question}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"\n[LIBRARIAN RESPONSE]:")
        for i, res in enumerate(data['results']):
            print(f"{i+1}. [{res['source']}] (Score: {res['score']:.2f})")
            print(f"   Text: {res['text'][:150]}...\n")
    else:
        print(f"[ERROR] {response.status_code}: {response.text}")

if __name__ == "__main__":
    query_librarian("What are the core hardware thresholds for OOM protection?")
