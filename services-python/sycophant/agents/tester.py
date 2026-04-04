import os
import sys
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from routing.gateway import InferenceGateway

class Tester:
    def __init__(self, project_id: str = "default"):
        self.project_id = project_id
        self.workspace_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), f"../../../staging/projects/{project_id}/workspace")
        )

    def write_tests(self, filename: str, external_feedback: str = None, attempt: int = 1) -> str:
        print(f"[TESTER] 🧪 Generating adversarial tests for node: {filename}...")
        file_path = os.path.join(self.workspace_dir, filename)

        if not os.path.exists(file_path):
            print(f"[TESTER ❌] Source file {filename} not found.")
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        system_prompt = (
            "You are the DEAN-OS QA Engineer. "
            "Write a complete, working `pytest` suite for the provided Python code. "
            "CRITICAL RULES: "
            "1. Output ONLY raw, executable Python code. "
            "2. DO NOT use markdown formatting. NO triple backticks (```). "
            "3. DO NOT write any conversational text."
        )

        module_name = filename.replace('.py', '')
        user_prompt = (
            f"# TARGET MODULE: {module_name}\n"
            f"# SOURCE CODE:\n{source_code}\n\n"
            f"# Write the pytest suite. Import it using `import {module_name}`.\n"
        )

        if external_feedback:
            user_prompt = f"CRITICAL ERROR IN PREVIOUS TEST SUITE:\n{external_feedback}\n\nFix these errors.\n\n" + user_prompt

        try:
            gateway = InferenceGateway()
            response = gateway.generate(system=system_prompt, prompt=user_prompt, attempt=attempt)
            raw_output = response['response'].strip()

            compiled_code = self._compile_code(raw_output)
            if compiled_code:
                dirname = os.path.dirname(filename)
                basename = os.path.basename(filename)
                test_filename = os.path.join(dirname, f"test_{basename}") if dirname else f"test_{basename}"
                test_file_path = os.path.join(self.workspace_dir, test_filename)

                os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
                with open(test_file_path, "w", encoding="utf-8") as f:
                    f.write(compiled_code)

                print(f"[TESTER] ✅ Tests saved to {test_filename}.")
                return test_file_path
            else:
                raise ValueError("Could not extract Pytest code.")

        except Exception as e:
            print(f"[TESTER ❌] Fatal Error: {e}")
            return None

    def _compile_code(self, text: str) -> str:
        return text.strip()
