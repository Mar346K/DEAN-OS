import sys
import os
import json

# Ensure we can import our agents
sys.path.append(os.path.dirname(__file__))

from agents.architect import Architect
from agents.coder import MainCoder
from agents.tester import Tester
from agents.analyzer import Analyzer
from agents.deployer import Deployer

# [PHASE 11] The Self-Healing limit
MAX_RETRIES = 3

class AssemblyLine:
    def __init__(self):
        print("[MANAGER] Booting DEAN-OS Assembly Line...")
        self.architect = Architect()
        self.coder = MainCoder()
        self.tester = Tester()
        self.analyzer = Analyzer()
        self.deployer = Deployer()

    def build_project(self, intent: str):
        print(f"\n[MANAGER] Processing User Intent: '{intent}'")

        # --- Phase 1: Architecture ---
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

            # [PHASE 11 UPGRADE] The Recursive Debugging Loop
            for attempt in range(1, MAX_RETRIES + 1):
                if attempt > 1:
                    print(f"\n[MANAGER] 🔄 Initiating Self-Healing Loop (Attempt {attempt}/{MAX_RETRIES}) for {filename}...")

                # 1. Write the Code (Injecting feedback if this is a retry)
                source_path = self.coder.write_module(blueprint, file_spec, feedback=feedback)
                if not source_path:
                    print(f"[MANAGER] Skipping {filename} due to Coder failure.")
                    break

                # 2. Write the Tests (Injecting feedback if this is a retry)
                test_path = self.tester.write_tests(filename, feedback=feedback)
                if not test_path:
                    print(f"[MANAGER] Skipping QA for {filename} due to Tester failure.")
                    break

                # 3. Execute QA in the Sandbox
                test_filename = f"test_{filename}"
                report = self.analyzer.evaluate_code(test_filename)

                # 4. Evaluate and Route
                if report.get("status") == "pass":
                    self.deployer.deploy_module(filename)
                    success = True
                    break  # Escape the retry loop! The file is perfect.
                else:
                    print(f"[MANAGER ⚠️] QA Failed on Attempt {attempt}.")
                    # Capture the raw tracebacks to feed back into the AI on the next loop
                    feedback = report.get("logs", "Unknown error occurred.")

            # If we exhausted all 3 retries and it still failed
            if not success:
                print(f"\n[MANAGER 🛑] QUARANTINE: {filename} failed QA after {MAX_RETRIES} attempts.")
                print("It has been left in 'staging/workspace/' for human review. It will NOT be deployed.")

        print("\n[MANAGER] Assembly Line run complete. Check 'workspace/' for production-ready files.")

if __name__ == "__main__":
    manager = AssemblyLine()

    # The Ultimate Test
    prompt = "Build a modular terminal Blackjack game with CSV save states for player bankrolls."
    manager.build_project(intent=prompt)
