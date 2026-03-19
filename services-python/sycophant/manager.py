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

            # 1. Write the Code
            source_path = self.coder.write_module(blueprint, file_spec)
            if not source_path:
                print(f"[MANAGER] Skipping {filename} due to Coder failure.")
                continue

            # 2. Write the Tests
            test_path = self.tester.write_tests(filename)
            if not test_path:
                print(f"[MANAGER] Skipping QA for {filename} due to Tester failure.")
                continue

            # 3. Execute QA in the Sandbox
            test_filename = f"test_{filename}"
            report = self.analyzer.evaluate_code(test_filename)

            # 4. Deployment or Quarantine
            if report.get("status") == "pass":
                self.deployer.deploy_module(filename)
            else:
                # In Phase 11, this will trigger the Recursive Debugging loop.
                # For now, we quarantine the bad code in staging.
                print(f"\n[MANAGER ⚠️] QUARANTINE: {filename} failed QA.")
                print("It has been left in 'staging/workspace/' for human review. It will NOT be deployed.")

        print("\n[MANAGER] Assembly Line run complete. Check 'workspace/' for production-ready files.")

if __name__ == "__main__":
    manager = AssemblyLine()

    # The Ultimate Test: Build the entire Blackjack game autonomously
    prompt = "Build a modular terminal Blackjack game with CSV save states for player bankrolls."
    manager.build_project(intent=prompt)
