import ollama
import os
import re

class Tester:
    def __init__(self, model_name="llama3.1:latest"):
        self.model_name = model_name
        # Absolute path to the staging area
        self.workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../staging/workspace"))

    def _strip_markdown(self, text: str) -> str:
        """Removes ```python and ``` blocks if the model hallucinates them."""
        text = re.sub(r"^```python\s*", "", text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r"^```\w*\s*", "", text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r"```$", "", text, flags=re.MULTILINE)
        return text.strip()

    # [FIX] Added 'feedback' parameter
    def write_tests(self, filename: str, feedback: str = None) -> str:
        print(f"[TESTER] Generating adversarial tests for: {filename}...")
        file_path = os.path.join(self.workspace_dir, filename)

        if not os.path.exists(file_path):
            print(f"[TESTER ERROR] Source file {filename} not found in workspace.")
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        system_prompt = (
            "You are the DEAN-OS Lead QA Engineer. Your job is to write rigorous, "
            "adversarial pytest test cases for the provided Python module.\n\n"
            "CRITICAL RULES:\n"
            "1. Output ONLY the raw Python code. No markdown formatting, no conversational text.\n"
            "2. Use the standard 'pytest' framework. If testing file IO, use the 'tmp_path' fixture. "
            "If the target module uses `input()`, you MUST mock it using `@patch('builtins.input')`.\n"
            "3. Include happy path and edge case validations.\n"
            "4. Ensure your import statements match the target module."
        )

        module_name = filename.replace('.py', '')

        user_prompt = (
            f"TARGET MODULE: {module_name}\n\n"
            f"SOURCE CODE TO TEST:\n{source_code}\n\n"
            f"Write a comprehensive pytest suite for this code. Import it using `import {module_name}` "
            f"or `from {module_name} import ...`.\n"
        )

        # [FIX] Inject QA feedback if the tests themselves contained syntax errors
        if feedback:
            print(f"[TESTER] ⚠️ Processing feedback from previous failure...")
            user_prompt += f"\n\nCRITICAL ERROR FEEDBACK:\nYour previous test suite failed with the following errors:\n{feedback}\n\nRewrite the test suite to fix these errors. REMEMBER: No conversational text!\n"

        user_prompt += "\nBEGIN RAW PYTHON CODE:"

        # ... (keep the rest of the try/except block exactly the same) ...
        try:
            response = ollama.generate(
                model=self.model_name,
                system=system_prompt,
                prompt=user_prompt
            )

            raw_code = self._strip_markdown(response['response'])

            # Prepend 'test_' to the filename to match pytest discovery rules
            test_filename = f"test_{filename}"
            test_file_path = os.path.join(self.workspace_dir, test_filename)

            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(raw_code)

            print(f"[TESTER SUCCESS] Saved {test_filename} to workspace.")
            return test_file_path

        except Exception as e:
            print(f"[TESTER ERROR] Failed to write tests for {filename}: {e}")
            return None
