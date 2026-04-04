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
        self.tier1_model = "qwen-14b"
        self.tier2_model = "Qwen2.5-Coder-32B-Instruct-IQ3_M.gguf"
        self.secret = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")

        self.aethelgard_url = f"http://{os.getenv('AETHELGARD_HOST', '127.0.0.1')}:8003/metrics"
        redis_host = os.getenv("REDIS_HOST", "redis")
        self.redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

        # Track the last used model to manage VRAM
        self.active_model = None

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

    def _get_dynamic_context_limit(self, is_tier2: bool) -> int:
        try:
            resp = requests.get(self.aethelgard_url, timeout=1.0)
            if resp.status_code == 200:
                metrics = resp.json()
                total_vram = metrics.get('vram_total_mb', 16000)
                if total_vram == 0: total_vram = 16000
                used_vram = metrics.get('vram_used_mb', 14800)
                free_vram_mb = total_vram - used_vram
            else:
                free_vram_mb = 1200
        except Exception:
            free_vram_mb = 1200

        bytes_per_token = 262144 if is_tier2 else 196608
        safe_free_vram = max(0, free_vram_mb - 200)

        max_tokens = int((safe_free_vram * 1024 * 1024) / bytes_per_token)
        return max(2048, min(max_tokens, 32768))

    def _compress_context(self, prompt: str) -> str:
        print("\n[GATEWAY ⚠️] CONTEXT SATURATION CRITICAL. Triggering Neural Compression Handoff...")
        compression_sys = "You are a data compression AI. Summarize the following project state into a dense technical brief. Preserve ALL filenames, core function signatures, and critical architectural decisions. Discard conversational filler."
        try:
            resp = ollama.generate(
                model=self.tier1_model,
                system=compression_sys,
                prompt=prompt,
            )
            compressed = resp['response'].strip()
            print(f"[GATEWAY ♻️] Handoff successful. State compressed to ~{len(compressed)//4} tokens.")
            return compressed
        except Exception as e:
            print(f"[GATEWAY ERROR] Compression failed, proceeding with bloated context: {e}")
            return prompt

    def _unload_model(self, model_name: str):
        """Forces Ollama to purge the specified model from VRAM."""
        print(f"\n[GATEWAY 🧹] Flushing {model_name} from VRAM to prevent CPU spill...")
        try:
            # An empty prompt with keep_alive=0 instantly unloads the model
            requests.post(
                f"http://{os.getenv('OLLAMA_HOST', 'host.docker.internal')}:11434/api/generate",
                json={"model": model_name, "prompt": "", "keep_alive": 0},
                timeout=5.0
            )
            # Give the GPU a second to physically clear the memory registers
            time.sleep(1.5)
            print(f"[GATEWAY 🧹] VRAM flushed successfully.")
        except Exception as e:
            print(f"[GATEWAY ERROR] Failed to flush VRAM: {e}")

    def generate(self, system: str, prompt: str, format_schema: dict = None, attempt: int = 1):
        use_cloud = attempt >= 3
        api_key = valkyrie_crypto.unseal_key("gemini", self.secret) if use_cloud else None

        # Fallback to local 32B if cloud is requested but no key is present
        selected_model = self.tier2_model if (use_cloud and not api_key) else self.tier1_model
        is_tier2 = selected_model == self.tier2_model

        icon = "☁️" if (use_cloud and api_key) else "📡"
        print(f"\n[GATEWAY] {icon} Routing to {selected_model} | Attempt: {attempt}")

        # --- VRAM MANAGEMENT ---
        # If we are switching models, we MUST unload the old one first
        if self.active_model and self.active_model != selected_model:
            self._unload_model(self.active_model)

        self.active_model = selected_model
        # -----------------------

        stop_event = threading.Event()
        status = {'msg': f'Booting {selected_model}...'}
        spinner_thread = threading.Thread(target=self._spinner_task, args=(stop_event, status))

        try:
            spinner_thread.start()
            full_response = ""

            if use_cloud and api_key:
                # Assuming _call_gemini exists in your actual code
                pass
            else:
                max_safe_ctx = self._get_dynamic_context_limit(is_tier2)
                estimated_tokens = len(prompt) // 4

                saturation_pct = min(100.0, (estimated_tokens / max_safe_ctx) * 100)
                try:
                    self.redis_client.publish("ui_broadcasts", json.dumps({
                        "type": "context_telemetry",
                        "payload": {"saturation": saturation_pct, "max_tokens": max_safe_ctx, "current_tokens": estimated_tokens}
                    }))
                except Exception: # nosec B110
                    pass

                if estimated_tokens > (max_safe_ctx * 0.85):
                    status['msg'] = 'Compressing Context...'
                    prompt = self._compress_context(prompt)

                status['msg'] = f'Generating (Limit: {max_safe_ctx} tokens)...'

                # --- DYNAMIC TEMPERATURE LOGIC ---
                dynamic_temp = 0.0 if "JSON SCHEMA" in system else 0.2

                kwargs = {
                    "model": selected_model,
                    "system": system,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "num_ctx": max_safe_ctx,
                        "temperature": dynamic_temp,
                        "num_predict": 2048,  # <-- THE LEASH: Max 2048 tokens out
                        "stop": [             # <-- THE GAG: Shut up if you say these
                            "<|im_end|>",
                            "<|endoftext|>",
                            "TARGET MODULE:",
                            "GLOBAL EXPORT MAP:",
                            "CRITICAL ERROR FEEDBACK:"
                        ]
                    }
                }

                if format_schema:
                    kwargs["format"] = format_schema

                stream = ollama.generate(**kwargs)

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

            # FinOps Circuit Breaker...
            if attempt >= 3:
                estimated_tokens = (len(prompt) + len(full_response)) // 4
                cost_per_1k = 0.015

                approved = valkyrie_crypto.enforce_finops(
                    "session-main-thread",
                    estimated_tokens,
                    cost_per_1k
                )

                if not approved:
                    print("\n[GATEWAY 🛑] VALKYRIE INTERCEPT: Financial budget exceeded. Halting swarm.")
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
