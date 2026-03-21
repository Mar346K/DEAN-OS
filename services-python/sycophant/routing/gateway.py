import ollama
import sys
import time
import threading

class InferenceGateway:
    def __init__(self):
        # The ultra-fast coding specialist
        self.tier1_model = "qwen2.5-coder:7b"

        # The heavy-duty closer
        self.tier2_model = "qwen2.5-coder:14b"

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

    def generate(self, system: str, prompt: str, format_schema: dict, attempt: int = 1):
        selected_model = self.tier2_model if attempt >= 3 else self.tier1_model
        icon = "🚀" if attempt >= 3 else "📡"
        print(f"[GATEWAY] {icon} Routing to Tier-{1 if attempt < 3 else 2} ({selected_model}) | Attempt: {attempt}")

        stop_event = threading.Event()
        status = {'msg': f'Cold Starting / Loading {selected_model}...'}
        spinner_thread = threading.Thread(target=self._spinner_task, args=(stop_event, status))

        try:
            spinner_thread.start()
            stream = ollama.generate(
                model=selected_model,
                system=system,
                prompt=prompt,
                format=format_schema,
                stream=True
            )

            full_response = ""
            first_token = True

            for chunk in stream:
                if first_token:
                    # Kill the spinner the moment the first character drops
                    stop_event.set()
                    spinner_thread.join()
                    # Start streaming in a dim gray color so it doesn't clutter the main logs
                    sys.stdout.write("\n\033[90m")
                    first_token = False

                # Print the AI's thoughts live to the terminal
                sys.stdout.write(chunk['response'])
                sys.stdout.flush()
                full_response += chunk['response']

            # Reset terminal color back to normal
            sys.stdout.write("\033[0m\n")

            print(f"[GATEWAY] ✅ Generation complete ({len(full_response)} chars).")
            return {'response': full_response}

        except KeyboardInterrupt:
            stop_event.set()
            if spinner_thread.is_alive():
                spinner_thread.join()
            sys.stdout.write("\033[0m\n")
            print(f"\n[GATEWAY 🛑] Inference aborted by user (Ctrl+C).")
            raise KeyboardInterrupt
        except Exception as e:
            stop_event.set()
            if spinner_thread.is_alive():
                spinner_thread.join()
            sys.stdout.write("\033[0m\n")
            print(f"\n[GATEWAY ERROR] Failed to generate via {selected_model}: {e}")
            raise e
