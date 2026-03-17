import httpx
import asyncio
import valkyrie_crypto  # The Rust Bridge
import ollama           # Local AI Power
from pydantic import BaseModel

# --- CONFIG ---
SECRET = "daen-internal-dev-secret-2026"  # nosec B105
MNEMOSYNE_URL = "http://127.0.0.1:8001"
OUBLIETTE_URL = "http://127.0.0.1:8002"
MODEL_NAME = "llama3.1:latest"
MAX_RETRIES = 3  # The Agent gets 3 tries to get it right

async def execute_task(query: str):
    print(f"\n[SYCOPHANT] Intent Received: '{query}'")

    # 1. SECURITY: Forge high-clearance identity
    token = valkyrie_crypto.forge_token("sycophant-core", "admin", SECRET)
    headers = {"Authorization": f"Bearer {token}"}

    # Increased timeout because LLMs can take a few seconds to think
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 2. KNOWLEDGE: Search Mnemosyne for truth
        print("[SYCOPHANT] Searching Knowledge Vault...")
        try:
            memory_resp = await client.post(
                f"{MNEMOSYNE_URL}/search",
                params={"query": query},
                headers=headers
            )
            results = memory_resp.json().get("results", [])
            context = results[0]["text"] if results else "No specific documentation found."
        except Exception as e:
            print(f"[SYCOPHANT] Warning: Mnemosyne unreachable - {e}")
            context = "No context available."

        system_prompt = (
            "You are the DEAN-OS Executive. Your task is to write Python code "
            "to solve the user's problem based on the provided context. "
            "Output ONLY raw Python code. No markdown, no backticks, no comments."
        )
        user_prompt = f"Context: {context}\n\nTask: {query}"

        # 3 & 4. THE SELF-HEALING LOOP (Reasoning & Execution)
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"\n[SYCOPHANT] --- Generation Attempt {attempt}/{MAX_RETRIES} ---")
            print(f"[SYCOPHANT] Consulting {MODEL_NAME}...")

            response = ollama.generate(
                model=MODEL_NAME,
                system=system_prompt,
                prompt=user_prompt
            )
            generated_code = response['response'].strip()

            # Clean up any markdown
            generated_code = generated_code.replace("```python", "").replace("```", "").strip()
            print(f"[SYCOPHANT] Strategy Drafted ({len(generated_code)} chars)")

            print("[SYCOPHANT] Deploying to Sandbox...")
            sandbox_resp = await client.post(
                f"{OUBLIETTE_URL}/run",
                json={"code": generated_code},
                headers=headers
            )

            if sandbox_resp.status_code != 200:
                return {"error": f"HTTP {sandbox_resp.status_code}", "details": sandbox_resp.text}

            result = sandbox_resp.json()

            # Did the Sandbox catch a crash?
            if "error" in result:
                error_msg = result.get('details', 'Unknown execution error')
                print(f"[SYCOPHANT] Sandbox rejected execution:\n{error_msg.strip()}")

                if attempt < MAX_RETRIES:
                    print("[SYCOPHANT] Initiating Self-Healing Protocol...")
                    # FEED THE ERROR BACK TO THE LLM
                    user_prompt += (
                        f"\n\nWARNING: The previous code failed with this error:\n{error_msg}\n"
                        "Please rewrite the Python code to fix this. If it was a ModuleNotFoundError, "
                        "you MUST use ONLY standard built-in Python libraries (like os, sys, subprocess). "
                        "Output ONLY raw Python code."
                    )
                else:
                    print("[SYCOPHANT] Max retries reached. Task failed.")
                    return result
            else:
                print("[SYCOPHANT] Execution Successful on Sandbox!")
                return result

if __name__ == "__main__":
    user_input = "Check the OOM thresholds and print a status report."
    result = asyncio.run(execute_task(user_input))

    if "error" in result:
        print(f"\n[FINAL SYSTEM REPORT]: EXECUTION FAILED\n{result.get('details')}")
    else:
        print(f"\n[FINAL SYSTEM REPORT]: SUCCESS\n{result.get('output')}")
