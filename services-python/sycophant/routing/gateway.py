import sys
import time
import threading
import os
import json
import requests
import redis
import valkyrie_crypto
import ollama

class InferenceGateway:
    def __init__(self):
        # --- THE SOVEREIGN FACTORY FLEET ---
        self.local_coder = "qwen-14b" # Offline fallback

        # OpenRouter Fleet
        self.cloud_coder = "qwen/qwen-2.5-coder-32b-instruct"  # The Workhorse
        self.cloud_librarian = "nvidia/nemotron-4-340b-instruct" # The Memory/Zip

        # Google Direct
        self.cloud_simulator = "gemini-2.5-flash" # The Digital Twin
        # -----------------------------------

        self.secret = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")
        self.aethelgard_url = f"http://{os.getenv('AETHELGARD_HOST', '127.0.0.1')}:8003/metrics"

        redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
        self.redis_client = redis.Redis(host=redis_host, port=6380 if redis_host == "127.0.0.1" else 6379, db=0, decode_responses=True)

    def _spinner_task(self, stop_event, status_dict):
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        idx = 0
        while not stop_event.is_set():
            msg = status_dict.get('msg', 'Routing prompt...')
            sys.stdout.write(f"\r\033[K[GATEWAY] {spinner_chars[idx]} {msg}")
            sys.stdout.flush()
            idx = (idx + 1) % len(spinner_chars)
            time.sleep(0.1)
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    def _call_openrouter(self, model: str, system: str, prompt: str, api_key: str, temperature: float) -> str:
        """Standardized OpenClaw/OpenRouter Interop Protocol"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://deanos.local",
            "X-Title": "DEAN-OS v5.1",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": 4096
        }

        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=60.0)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']

    def generate(self, system: str, prompt: str, task_type: str = "CODE_GEN", attempt: int = 1):
        """
        The Master Switchboard.
        task_type options: 'CODE_GEN', 'INGEST', 'SIMULATE'
        """
        # Unseal the required keys
        openrouter_key = valkyrie_crypto.unseal_key("openrouter", self.secret)
        gemini_key = valkyrie_crypto.unseal_key("gemini", self.secret)

        # 1. ROUTING LOGIC
        use_local = False
        if task_type == "INGEST" and openrouter_key:
            selected_model = self.cloud_librarian
            api_key = openrouter_key
            platform = "openrouter"
        elif task_type == "SIMULATE" and gemini_key:
            selected_model = self.cloud_simulator
            api_key = gemini_key
            platform = "gemini"
        elif task_type == "CODE_GEN" and openrouter_key:
            selected_model = self.cloud_coder
            api_key = openrouter_key
            platform = "openrouter"
        else:
            # Absolute fallback to local physics
            selected_model = self.local_coder
            use_local = True
            platform = "ollama"

        icon = "🧠" if platform == "openrouter" else ("☁️" if platform == "gemini" else "🖥️")
        print(f"\n[GATEWAY] {icon} Task: {task_type} | Routing to {selected_model} (Attempt {attempt})")

        stop_event = threading.Event()
        status = {'msg': f'Transmitting to {selected_model}...'}
        spinner_thread = threading.Thread(target=self._spinner_task, args=(stop_event, status))

        try:
            spinner_thread.start()
            dynamic_temp = 0.0 if "JSON SCHEMA" in system else 0.2
            full_response = ""

            # 2. EXECUTION
            if platform == "openrouter":
                full_response = self._call_openrouter(selected_model, system, prompt, api_key, dynamic_temp)

            elif platform == "gemini":
                # We reuse the existing REST call logic for Gemini
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={api_key}"
                payload = {
                    "system_instruction": {"parts": [{"text": system}]},
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": dynamic_temp}
                }
                resp = requests.post(url, json=payload, timeout=30.0)
                resp.raise_for_status()
                full_response = resp.json()['candidates'][0]['content']['parts'][0]['text']

            elif platform == "ollama":
                # Local fallback execution (with the gag from the previous fix)
                stream = ollama.generate(
                    model=selected_model,
                    system=system,
                    prompt=prompt,
                    stream=True,
                    options={"temperature": dynamic_temp, "num_predict": 2048, "stop": ["<|im_end|>", "TARGET MODULE:"]}
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

            # Clean up the output if it accidentally spits markdown
            if "```python" in full_response:
                full_response = full_response.split("```python")[1].split("```")[0]

            print(f"[GATEWAY] ✅ {task_type} payload received ({len(full_response)} chars).")
            return {'response': full_response.strip()}

        except Exception as e:
            print(f"\n[GATEWAY ❌] Transmission Failed: {e}")
            raise e
        finally:
            stop_event.set()
            if spinner_thread.is_alive():
                spinner_thread.join()
