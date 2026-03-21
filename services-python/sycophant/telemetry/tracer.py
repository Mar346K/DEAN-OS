import uuid
import time
import requests
from contextlib import contextmanager

class TelemetryEngine:
    def __init__(self):
        # Generate a unique 8-character ID for the entire lifecycle of the user prompt
        self.current_trace_id = str(uuid.uuid4())[:8]
        # The URL for our Rust Governor (Aethelgard)
        self.aethelgard_url = "http://127.0.0.1:8003/trace"

    @contextmanager
    def span(self, agent_name: str, action: str):
        """
        A context manager to track the exact execution time and status of an agent's task.
        Outputs a color-coded Waterfall trace to the terminal.
        """
        start_time = time.time()

        # ANSI colors for a beautiful 'Glass-Box' CLI
        TRACE_COLOR = "\033[95m"  # Magenta
        AGENT_COLOR = "\033[96m"  # Cyan
        RESET = "\033[0m"

        print(f"\n[{TRACE_COLOR}TRACE:{self.current_trace_id}{RESET}] ⏳ {AGENT_COLOR}{agent_name}{RESET} is initiating: {action}...")

        try:
            # Yield control back to the agent to do its work
            yield self.current_trace_id

            # Success Path
            latency = time.time() - start_time
            print(f"[{TRACE_COLOR}TRACE:{self.current_trace_id}{RESET}] ✅ {AGENT_COLOR}{agent_name}{RESET} completed in {latency:.2f}s.")

        except Exception as e:
            # Failure Path
            latency = time.time() - start_time
            print(f"[{TRACE_COLOR}TRACE:{self.current_trace_id}{RESET}] ❌ \033[91m{agent_name} FAILED\033[0m after {latency:.2f}s. Error: {e}")
            raise e

    def record_hop(self, source: str, target: str):
        """
        Reports agent-to-agent delegation to the Aethelgard Rust Governor
        for DAG Deadlock Prevention (Phase 13 Integration).
        """
        payload = {
            "trace_id": self.current_trace_id,
            "source_agent": source,
            "target_agent": target
        }
        try:
            # 50ms timeout: Telemetry should NEVER slow down or crash the main application
            requests.post(self.aethelgard_url, json=payload, timeout=0.05)
        except Exception:
            pass # nosec B110
