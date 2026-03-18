import httpx
import asyncio
import valkyrie_crypto
import ollama
import os
import json
import time

# --- CONFIG ---
SECRET = "daen-internal-dev-secret-2026"  # nosec B105
MNEMOSYNE_URL = "http://127.0.0.1:8001"
OUBLIETTE_URL = "http://127.0.0.1:8002"
AETHELGARD_URL = "http://127.0.0.1:8003/metrics" # <-- The Governor
MODEL_NAME = "llama3.1:latest"
MAX_RETRIES = 3

def get_installed_tools():
    dockerfile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../infrastructure/containers/sandbox.Dockerfile"))
    try:
        with open(dockerfile_path, "r") as f:
            for line in f:
                if line.startswith("RUN pip install"):
                    parts = line.strip().split(" ")
                    packages = [p for p in parts if not p.startswith("-") and p not in ["RUN", "pip", "install"]]
                    return ", ".join(packages)
    except FileNotFoundError:
        pass
    return "standard built-in libraries only"

async def check_hardware_status():
    """Ask Aethelgard for permission to execute."""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                resp = await client.get(AETHELGARD_URL, timeout=2.0)
                if resp.status_code == 200:
                    metrics = resp.json()
                    if metrics.get("status") == "CRITICAL":
                        print(f"\n[GOVERNOR INTERCEPT] Hardware under heavy load (RAM: {metrics.get('ram_usage_percent'):.1f}%). Throttling AI execution for 5 seconds...")
                        await asyncio.sleep(5)
                        continue
                    else:
                        print(f"[GOVERNOR APPROVED] Hardware Healthy (RAM: {metrics.get('ram_usage_percent'):.1f}%).")
                        return True
            except Exception:
                print("[WARNING] Aethelgard Governor unreachable. Bypassing safety checks...")
                return True

async def execute_task(query: str):
    print(f"\n[SYCOPHANT] Intent Received: '{query}'")

    token = valkyrie_crypto.forge_token("sycophant-core", "admin", SECRET)
    headers = {"Authorization": f"Bearer {token}"}
    installed_tools = get_installed_tools()

    async with httpx.AsyncClient(timeout=60.0) as client:
        print("[SYCOPHANT] Searching Knowledge Vault...")
        try:
            memory_resp = await client.post(
                f"{MNEMOSYNE_URL}/search",
                params={"query": query},
                headers=headers
            )
            results = memory_resp.json().get("results", [])
            context = "\n\n--- NEXT KNOWLEDGE CHUNK ---\n\n".join([r["text"] for r in results]) if results else "No specific documentation found."
        except Exception as e:
            print(f"[SYCOPHANT] Warning: Mnemosyne unreachable - {e}")
            context = "No context available."

        system_prompt = (
            "You are the DEAN-OS Executive. Your task is to write Python code to solve the user's problem. "
            "Output ONLY raw Python code. No markdown, no comments. "
            "CRITICAL RULES:\n"
            "1. You MUST base your solution STRICTLY on the text provided in the Context below.\n"
            "2. If the Context DOES NOT contain the information needed to answer the prompt, DO NOT hallucinate or guess. "
            "Instead, output exactly this JSON format: {\"knowledge_request\": \"Describe what information you are missing\"}\n"
            f"3. The Sandbox currently has these libraries installed: {installed_tools}. "
            "If the task requires an external pip library NOT listed, output: {\"tool_request\": \"library_name\"}"
        )
        user_prompt = f"User Query: {query}\n\nContext:\n{context}"

        for attempt in range(1, MAX_RETRIES + 1):
            print(f"\n[SYCOPHANT] --- Generation Attempt {attempt}/{MAX_RETRIES} ---")

            # ---> HARDWARE CHECK BEFORE AI GENERATION <---
            await check_hardware_status()

            print(f"[SYCOPHANT] Consulting {MODEL_NAME}...")

            response = ollama.generate(
                model=MODEL_NAME,
                system=system_prompt,
                prompt=user_prompt
            )
            generated_code = response['response'].strip()

            generated_code = generated_code.replace("```python", "").replace("```", "").strip()

            if generated_code.startswith("{"):
                try:
                    request_data = json.loads(generated_code)
                    if "tool_request" in request_data:
                        tool_name = request_data.get("tool_request")
                        print(f"\n[SYCOPHANT] LLM halted execution. Requesting external tool: '{tool_name}'")
                        staging_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../staging"))
                        os.makedirs(staging_dir, exist_ok=True)
                        with open(os.path.join(staging_dir, "quarantine_queue.txt"), "a") as f:
                            f.write(f"{tool_name}\n")
                        return {"status": "Quarantine Request Logged", "tool": tool_name}

                    elif "knowledge_request" in request_data:
                        missing_info = request_data.get("knowledge_request")
                        print(f"\n[SYCOPHANT] ⚠️ KNOWLEDGE GAP DETECTED: The AI says it is missing: '{missing_info}'")
                        human_help = input("[DEAN-OS] Please provide the missing context (or press Enter to fail): ")
                        if not human_help:
                            return {"error": "Human aborted knowledge request."}

                        print("[SYCOPHANT] Re-evaluating with Human Intel...")
                        user_prompt += f"\n\n[HUMAN OVERRIDE CONTEXT]: {human_help}\nPlease try writing the script again using this new info."
                        continue

                except json.JSONDecodeError:
                    print("[SYCOPHANT] Error decoding JSON.")

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
                        "Please rewrite the Python code to fix this."
                    )
                else:
                    print("[SYCOPHANT] Max retries reached. Task failed.")
                    return result
            else:
                print("[SYCOPHANT] Execution Successful on Sandbox!")
                return result

if __name__ == "__main__":
    user_input = "Based ONLY on the provided context, write a python script that prints out the 5 Traceability Markers of the Memory Vault and their descriptions."
    result = asyncio.run(execute_task(user_input))

    if "error" in result:
        print(f"\n[FINAL SYSTEM REPORT]: EXECUTION FAILED\n{result.get('details', result)}")
    else:
        print(f"\n[FINAL SYSTEM REPORT]: SUCCESS\n{result}")
