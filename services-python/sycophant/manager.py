import sys
import os

# Ensure we can import our agents
sys.path.append(os.path.dirname(__file__))

from agents.architect import Architect
from agents.coder import MainCoder
from agents.tester import Tester
from agents.analyzer import Analyzer
from agents.deployer import Deployer
from telemetry.tracer import TelemetryEngine
from telemetry.watchdog import SystemWatchdog

# [PHASE 11] The Self-Healing limit
MAX_RETRIES = 3

class AssemblyLine:
    def __init__(self):
        print("[MANAGER] Booting DEAN-OS Assembly Line...")
        self.tracer = TelemetryEngine()
        self.architect = Architect()
        self.coder = MainCoder()
        self.tester = Tester()
        self.analyzer = Analyzer()
        self.deployer = Deployer()

    def build_project(self, intent: str):
        print(f"\n[MANAGER] Processing User Intent: '{intent}'")

        # --- Phase 1: Architecture ---
        with self.tracer.span("Architect", f"Drafting blueprint for intent: '{intent}'"):
            blueprint = self.architect.draft_plan(user_intent=intent)

        if not blueprint:
            print("[MANAGER ERROR] Architect failed to produce a valid blueprint. Halting.")
            return

        files_to_build = blueprint.get("files", [])
        print(f"\n[MANAGER] Blueprint Approved. {len(files_to_build)} modules entering the production line.")

        # --- Phase 2: The Assembly Loop ---
        for file_spec in files_to_build:
            filename = file_spec.get("filename")
            print(f"\n{'='*50}\n[ASSEMBLY LINE] Processing: {filename}\n{'='*50}")

            feedback = None
            success = False
            attempt = 1
            dynamic_max_retries = MAX_RETRIES

            while attempt <= dynamic_max_retries:
                if attempt > 1:
                    print(f"\n[MANAGER] 🔄 Initiating Self-Healing Loop (Attempt {attempt}/{dynamic_max_retries}) for {filename}...")

                # 1. Write the Code
                with self.tracer.span("Coder", f"Writing implementation for {filename} (Attempt {attempt})"):
                    self.tracer.record_hop("Manager", "Coder")
                    source_path = self.coder.write_module(blueprint, file_spec, feedback=feedback, attempt=attempt)

                if not source_path:
                    print(f"[MANAGER] Skipping {filename} due to Coder failure.")
                    break

                # 2. Write the Tests
                with self.tracer.span("Tester", f"Generating adversarial tests for {filename} (Attempt {attempt})"):
                    self.tracer.record_hop("Manager", "Tester")
                    test_path = self.tester.write_tests(filename, feedback=feedback, attempt=attempt)

                if not test_path:
                    print(f"[MANAGER] Skipping QA for {filename} due to Tester failure.")
                    break

                # 3. Execute QA in the Sandbox
                test_filename = f"test_{filename}"
                with self.tracer.span("Analyzer", f"Evaluating {test_filename} in Oubliette"):
                    self.tracer.record_hop("Manager", "Analyzer")
                    report = self.analyzer.evaluate_code(test_filename)

                # 4. Evaluate and Route
                if report.get("status") == "pass":
                    with self.tracer.span("Deployer", f"Migrating {filename} to production"):
                        self.tracer.record_hop("Manager", "Deployer")
                        self.deployer.deploy_module(filename)
                        success = True
                    break  # Escape the retry loop!
                else:
                    print(f"[MANAGER ⚠️] QA Failed on Attempt {attempt}.")
                    feedback = report.get("logs", "Unknown error occurred.")

                    # --- PHASE 16: HITL Checkpoint Interceptor ---
                    if attempt == dynamic_max_retries:
                        print(f"\n[MANAGER 🛑] Sandbox execution failed {dynamic_max_retries} times.")
                        print(f"--- FAULT TRACEBACK ---\n{feedback}\n-----------------------")

                        # Serialize state to disk (Hard checkpoint)
                        checkpoint_data = {
                            "intent": intent,
                            "filename": filename,
                            "attempt": attempt,
                            "traceback": feedback
                        }
                        checkpoint_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../staging/checkpoint.json"))
                        with open(checkpoint_path, "w") as f:
                            import json
                            json.dump(checkpoint_data, f, indent=4)

                        # Await Human Guidance
                        print(f"\n[SYSTEM CHECKPOINT SAVED TO {checkpoint_path}]")
                        human_hint = input("[DEAN-OS HITL] Provide a hint to fix this (or press Enter to Quarantine): ")

                        if human_hint.strip():
                            print("\n[MANAGER] Human guidance received. Rebooting Assembly Line for this module...")
                            feedback += f"\n\n[HUMAN OPERATOR GUIDANCE]: {human_hint}"
                            dynamic_max_retries += 1  # Grant the AI one more attempt using the Tier-2 model
                        else:
                            print("\n[MANAGER] No human guidance provided. Proceeding to Quarantine.")

                attempt += 1

            # If we exhausted all retries and it still failed
            if not success:
                print(f"\n[MANAGER 🛑] QUARANTINE: {filename} failed QA after {dynamic_max_retries} attempts.")
                print("It has been left in 'staging/workspace/' for human review. It will NOT be deployed.")

        print("\n[MANAGER] Assembly Line run complete. Check 'workspace/' for production-ready files.")

if __name__ == "__main__":
    try:
        # --- PHASE 16: Pre-flight Check ---
        guard = SystemWatchdog()
        guard.run_preflight_check()
        # ----------------------------------

        manager = AssemblyLine()

        # The Ultimate Test
        prompt = "Build a modular terminal Blackjack game with CSV save states for player bankrolls."
        manager.build_project(intent=prompt)
    except KeyboardInterrupt:
        print("\n\n[MANAGER 🛑] System execution halted by user (Ctrl+C). Shutting down Assembly Line.")
        sys.exit(0)
