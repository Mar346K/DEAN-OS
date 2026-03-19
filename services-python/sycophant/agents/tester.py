import ollama
import os
import json

class Tester:
    def __init__(self, model_name="llama3.1:latest"):
        self.model_name = model_name
        self.workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../staging/workspace"))

    def write_tests(self, filename: str, feedback: str = None) -> str:
        print(f"[TESTER] Generating adversarial tests for: {filename}...")
        file_path = os.path.join(self.workspace_dir, filename)

        if not os.path.exists(file_path):
            print(f"[TESTER ERROR] Source file {filename} not found in workspace.")
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        # [PHASE 12 UPGRADE] The Grammar FSM Schema
        test_schema = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The raw pytest python code. Absolutely no markdown or conversational text."
                }
            },
            "required": ["code"]
        }

        system_prompt = (
            "You are the DEAN-OS Lead QA Engineer. "
            "You must output YOUR ENTIRE RESPONSE as a valid JSON object matching the requested schema. "
            "1. Use the standard 'pytest' framework.\n"
            "2. If testing file IO, use the 'tmp_path' fixture.\n"
            "3. If the target uses `input()`, mock it using `@patch('builtins.input')`.\n"
            "4. Include happy path and edge case validations."
        )

        module_name = filename.replace('.py', '')

        user_prompt = (
            f"TARGET MODULE: {module_name}\n\n"
            f"SOURCE CODE TO TEST:\n{source_code}\n\n"
            f"Write a comprehensive pytest suite for this code. Import it using `import {module_name}`.\n"
        )

        if feedback:
            print(f"[TESTER] ⚠️ Processing feedback from previous failure...")
            user_prompt += f"\n\nCRITICAL ERROR FEEDBACK:\nYour previous test suite failed with the following errors:\n{feedback}\n\nRewrite the test suite to fix these errors.\n"

        try:
            # format=test_schema forces FSM adherence
            response = ollama.generate(
                model=self.model_name,
                system=system_prompt,
                prompt=user_prompt,
                format=test_schema
            )

            result_json = json.loads(response['response'])
            raw_code = result_json.get("code", "")

            # [FIX] Handle subdirectories correctly for test files
            dirname = os.path.dirname(filename)
            basename = os.path.basename(filename)
            test_filename = os.path.join(dirname, f"test_{basename}") if dirname else f"test_{basename}"

            test_file_path = os.path.join(self.workspace_dir, test_filename)
            os.makedirs(os.path.dirname(test_file_path), exist_ok=True)

            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(raw_code)

            print(f"[TESTER SUCCESS] Saved {test_filename} to workspace.")
            return test_file_path

        except json.JSONDecodeError as e:
            print(f"[TESTER ERROR] FSM Violation - Invalid JSON returned: {e}")
            return None
        except Exception as e:
            print(f"[TESTER ERROR] Failed to write tests for {filename}: {e}")
            return None
