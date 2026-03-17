import httpx
import asyncio
import valkyrie_crypto  # The Rust Bridge
from pydantic import BaseModel

# --- CONFIG ---
# --- CONFIG ---
SECRET = "daen-internal-dev-secret-2026"  # nosec B105
MNEMOSYNE_URL = "http://127.0.0.1:8001"
OUBLIETTE_URL = "http://127.0.0.1:8002"

class TaskRequest(BaseModel):
    user_query: str

async def execute_task(query: str):
    print(f"[SYCOPHANT] Orchestrating task: {query}")

    # 1. SECURITY: Forge a high-clearance token via Rust
    token = valkyrie_crypto.forge_token("sycophant-admin", "superuser", SECRET)
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        # 2. KNOWLEDGE: Query Mnemosyne for technical context
        print("[SYCOPHANT] Consulted Mnemosyne for truth...")
        memory_resp = await client.post(
            f"{MNEMOSYNE_URL}/search",
            params={"query": query},
            headers=headers
        )
        context = memory_resp.json().get("results", [])
        top_context = context[0]["text"] if context else "No context found."

        # 3. REASONING: Placeholder for LLM
        # We use a raw string and repr() to avoid syntax errors from quotes in the context
        clean_context = top_context[:50].replace("'", "").replace('"', "")
        generated_script = f"print('Analysis based on context: {clean_context}')"

        # 4. EXECUTION: Send the script to the Oubliette
        print("[SYCOPHANT] Executing generated logic in Oubliette...")
        sandbox_resp = await client.post(
            f"{OUBLIETTE_URL}/run",
            params={"code": generated_script},
            headers=headers
        )

        return sandbox_resp.json()

if __name__ == "__main__":
    # Test a full loop
    result = asyncio.run(execute_task("What are the hardware thresholds?"))
    print(f"\n[FINAL RESULT]: {result}")
