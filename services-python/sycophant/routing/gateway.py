import ollama
import sys
import time
import threading

class InferenceGateway:
    def __init__(self):
        # Tier 1: Fast, Low-VRAM usage
        self.tier1_model = "llama3.1:latest"

        # Tier 2: The Logic Specialist (High Reasoning)
        self.tier2_model = "llama3.3:70b"

    def _spinner_task(self, stop_event, status_dict):
        """Background thread to animate the terminal while blocking."""
        # Braille spinner animation
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        idx = 0
        while not stop_event.is_set():
            msg = status_dict.get('msg', 'Processing...')
            # \r returns to start of line, \033[K clears the line so text doesn't overlap
            sys.stdout.write(f"\r\033[K[GATEWAY] {spinner_chars[idx]} {msg}")
            sys.stdout.flush()
            idx = (idx + 1) % len(spinner_chars)
            time.sleep(0.1)

        # Clear the spinner line completely when done
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    def generate(self, system: str, prompt: str, format_schema: dict, attempt: int = 1):
        """
        Dynamically escalates intelligence and displays a live heartbeat.
        """
        selected_model = self.tier2_model if attempt >= 3 else self.tier1_model

        icon = "🚀" if attempt >= 3 else "📡"
        print(f"[GATEWAY] {icon} Routing to Tier-{1 if attempt < 3 else 2} ({selected_model}) | Attempt: {attempt}")

        # Set up the background thread for the heartbeat animation
        stop_event = threading.Event()
        status = {'msg': f'Cold Starting / Loading {selected_model} into Memory...'}
        spinner_thread = threading.Thread(target=self._spinner_task, args=(stop_event, status))

        try:
            spinner_thread.start()

            # stream=True allows us to detect exactly when the model finishes loading
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
                    # The moment we get the first chunk, the model is fully loaded in RAM.
                    status['msg'] = f'Inference active. Generating tokens...'
                    first_token = False

                full_response += chunk['response']

            # Stop the spinner gracefully
            stop_event.set()
            spinner_thread.join()

            print(f"[GATEWAY] ✅ Generation complete ({len(full_response)} chars).")

            # Reconstruct the response dictionary to match the original API signature
            # so the Coder and Tester don't break.
            return {'response': full_response}

        except Exception as e:
            stop_event.set()
            if spinner_thread.is_alive():
                spinner_thread.join()
            print(f"\n[GATEWAY ERROR] Failed to generate via {selected_model}: {e}")
            raise e
