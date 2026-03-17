import httpx
import asyncio
import valkyrie_crypto
import ollama
from pydantic import BaseModel
import os
import json

# --- CONFIG ---
SECRET = "daen-internal-dev-secret-2026"  # nosec B105
MNEMOSYNE_URL = "http://127.0.0.1:8001"
OUBLIETTE_URL = "http://127.0.0.1:8002"
MODEL_NAME = "llama3.1:latest"
MAX_RETRIES = 3

async def execute_task(query: str):
    print(f"\n[SYCOPHANT] Intent Received: '{query}'")

    token = valkyrie_crypto.forge_token("sycophant-core", "admin", SECRET)
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=60.0) as client:
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
            "You are the DEAN-OS Executive. Your task is to write Python code to solve the user's problem. "
            "Output ONLY raw Python code. No markdown, no comments. "
            "CRITICAL: The Sandbox only has standard built-in Python libraries installed. "
            "If the task is mathematically impossible without an external pip library (like requests, beautifulsoup4, numpy, etc.), "
            "you MUST output exactly this JSON format and nothing else: {\"tool_request\": \"library_name\"}"
        )
        user_prompt = f"Context: {context}\n\nTask: {query}"

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

            # --- THE QUARANTINE INTERCEPTOR ---
            if generated_code.startswith("{") and "tool_request" in generated_code:
                try:
                    request_data = json.loads(generated_code)
                    tool_name = request_data.get("tool_request")
                    print(f"\n[SYCOPHANT] LLM halted execution. Requesting external tool: '{tool_name}'")

                    # Calculate absolute path to DEAN-OS/staging/
                    staging_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../staging"))
                    os.makedirs(staging_dir, exist_ok=True)
                    queue_file = os.path.join(staging_dir, "quarantine_queue.txt")

                    # Log the request
                    with open(queue_file, "a") as f:
                        f.write(f"{tool_name}\n")

                    return {"status": "Quarantine Request Logged", "tool": tool_name}
                except json.JSONDecodeError:
                    print("[SYCOPHANT] Error decoding tool request JSON. Falling back to execution attempt.")
            # ----------------------------------

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

            if "error" in result:
                error_msg = result.get('details', 'Unknown execution error')
                print(f"[SYCOPHANT] Sandbox rejected execution:\n{error_msg.strip()}")

                if attempt < MAX_RETRIES:
                    print("[SYCOPHANT] Initiating Self-Healing Protocol...")
                    user_prompt += (
                        f"\n\nWARNING: The previous code failed with this error:\n{error_msg}\n"
                        "Please rewrite the Python code to fix this. If it was a ModuleNotFoundError, "
                        "you MUST use ONLY standard built-in Python libraries (like os, sys, subprocess). "
                        "If the task is impossible without an external library, output the tool_request JSON."
                    )
                else:
                    print("[SYCOPHANT] Max retries reached. Task failed.")
                    return result
            else:
                print("[SYCOPHANT] Execution Successful on Sandbox!")
                return result

if __name__ == "__main__":
    # Test a query that forces the LLM to request a tool
    user_input = "Scrape the title of example.com using the BeautifulSoup library."
    result = asyncio.run(execute_task(user_input))

    if "error" in result:
        print(f"\n[FINAL SYSTEM REPORT]: EXECUTION FAILED\n{result.get('details')}")
    else:
        print(f"\n[FINAL SYSTEM REPORT]: SUCCESS\n{result}")
