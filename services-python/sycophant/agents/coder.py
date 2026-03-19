import ollama
import os
import re

class MainCoder:
    def __init__(self, model_name="llama3.1:latest"):
        self.model_name = model_name
        # Absolute path to the staging area
        self.workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../staging/workspace"))

    def _strip_markdown(self, text: str) -> str:
        """Removes ```python and ``` blocks if the model hallucinates them."""
        # Remove starting markdown
        text = re.sub(r"^```python\s*", "", text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r"^```\w*\s*", "", text, flags=re.IGNORECASE | re.MULTILINE)
        # Remove ending markdown
        text = re.sub(r"```$", "", text, flags=re.MULTILINE)
        return text.strip()

    def write_module(self, project_blueprint: dict, target_file: dict) -> str:
        filename = target_file.get("filename")
        print(f"[CODER] Writing implementation for: {filename}...")

        system_prompt = (
            "You are the DEAN-OS Lead Python Developer. You are part of an automated assembly line. "
            "You will be given a project blueprint and tasked with writing the code for ONE specific file.\n\n"
            "CRITICAL RULES:\n"
            "1. Output ONLY the raw Python code. Do not include markdown formatting (like ```python). "
            "Do not include conversational text, greetings, or explanations.\n"
            "2. Ensure you implement the exact function signatures requested in the blueprint.\n"
            "3. Include necessary imports.\n"
            "4. Write clean, production-ready code with basic docstrings."
        )

        user_prompt = (
            f"PROJECT BLUEPRINT:\n{project_blueprint}\n\n"
            f"YOUR TASK:\nWrite the complete implementation for the file: {filename}\n"
            f"Purpose: {target_file.get('purpose')}\n"
            f"Required Signatures: {target_file.get('signatures')}\n\n"
            "BEGIN RAW PYTHON CODE:"
        )

        try:
            response = ollama.generate(
                model=self.model_name,
                system=system_prompt,
                prompt=user_prompt
            )

            # Clean the output just in case the model ignores the markdown rule
            raw_code = self._strip_markdown(response['response'])

            # Write the file to the workspace
            file_path = os.path.join(self.workspace_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(raw_code)

            print(f"[CODER SUCCESS] Saved {filename} to workspace.")
            return file_path

        except Exception as e:
            print(f"[CODER ERROR] Failed to write module {filename}: {e}")
            return None
