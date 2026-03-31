import ollama
import sys
import time
import threading
import os
import json
import requests
import redis
import valkyrie_crypto

class InferenceGateway:
    def __init__(self):
        # The Qwen 14B Q4_K_M is the resident workhorse for speed and logic
        self.tier1_model = "qwen2.5-coder-14b-instruct-q4_k_m.gguf"
        # The Qwen 32B IQ3_M is summoned for heavy architecture design
        self.tier2_model = "Qwen2.5-Coder-32B-Instruct-IQ3_M.gguf"
        self.secret = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")

        # Connect to Redis to broadcast the kill signal directly to the UI
        redis_host = os.getenv("REDIS_HOST", "redis")
        self.redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

    def _spinner_task(self, stop_event, status_dict):
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        idx = 0
        while not stop_event.is_set():
            msg = status_dict.get('msg', 'Loading model to GPU...')
            sys.stdout.write(f"\r\033[K[GATEWAY] {spinner_chars[idx]} {msg}")
            sys.stdout.flush()
            idx = (idx + 1) % len(spinner_chars)
            time.sleep(0.1)
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    def _call_gemini(self, system: str, prompt: str, api_key: str, format_schema: dict):
        """Makes a direct REST call to Gemini, bypassing the need for extra SDKs."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.tier2_model}:generateContent?key={api_key}"

        # Gemini expects JSON schema natively
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "response_schema": format_schema
            }
        }

        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            raise Exception(f"Gemini API Error: {resp.text}")

    def generate(self, system: str, prompt: str, format_schema: dict, attempt: int = 1):
        use_cloud = attempt >= 3

        # Attempt to unseal the Gemini key if we are on attempt 3+
        api_key = None
        if use_cloud:
            api_key = valkyrie_crypto.unseal_key("gemini", self.secret)

        # Fallback to local if no key is vaulted
        selected_model = self.tier2_model if (use_cloud and api_key) else self.tier1_model
        icon = "☁️" if (use_cloud and api_key) else "📡"

        print(f"[GATEWAY] {icon} Routing to {selected_model} | Attempt: {attempt}")

        stop_event = threading.Event()
        status = {'msg': f'Booting {selected_model}...'}
        spinner_thread = threading.Thread(target=self._spinner_task, args=(stop_event, status))

        try:
            spinner_thread.start()
            full_response = ""

            # --- CLOUD ROUTE (GEMINI) ---
            if use_cloud and api_key:
                full_response = self._call_gemini(system, prompt, api_key, format_schema)
                stop_event.set()
                spinner_thread.join()
                # Print response since it wasn't streamed
                sys.stdout.write(f"\n\033[90m{full_response}\033[0m\n")

            # --- LOCAL ROUTE (OLLAMA) ---
            else:
                stream = ollama.generate(
                    model=selected_model,
                    system=system,
                    prompt=prompt,
                    format=format_schema,
                    stream=True
                )

                first_token = True
                for chunk in stream:
                    if first_token:
                        stop_event.set()
                        spinner_thread.join()
                        sys.stdout.write("\n\033[90m")
                        first_token = False
                    sys.stdout.write(chunk['response'])
                    sys.stdout.flush()
                    full_response += chunk['response']
                sys.stdout.write("\033[0m\n")

            # --- PHASE 16.2: FinOps Circuit Breaker ---
            if attempt >= 3:
                estimated_tokens = (len(prompt) + len(full_response)) // 4
                cost_per_1k = 0.015 # Proxy cost simulation

                approved = valkyrie_crypto.enforce_finops(
                    "session-main-thread",
                    estimated_tokens,
                    cost_per_1k
                )

                if not approved:
                    print("\n[GATEWAY 🛑] VALKYRIE INTERCEPT: Financial budget exceeded. Halting swarm.")

                    # [NEW] Broadcast the kill signal directly to the React UI
                    kill_msg = {
                        "type": "agent_trace",
                        "payload": {
                            "trace_id": "SYS-KILL",
                            "agent": "Valkyrie FinOps",
                            "action": "🛑 BUDGET EXCEEDED. CIRCUIT BREAKER TRIPPED. SWARM HALTED.",
                            "status": "error"
                        }
                    }
                    self.redis_client.publish("ui_broadcasts", json.dumps(kill_msg))

                    # Add a tiny sleep so Redis has time to dispatch before we violently kill the thread
                    time.sleep(0.5)
                    sys.exit(1)

            print(f"[GATEWAY] ✅ Generation complete ({len(full_response)} chars).")
            return {'response': full_response}

        except Exception as e:
            stop_event.set()
            if spinner_thread.is_alive():
                spinner_thread.join()
            sys.stdout.write("\033[0m\n")
            print(f"\n[GATEWAY ERROR] Failed to generate via {selected_model}: {e}")
            raise e
