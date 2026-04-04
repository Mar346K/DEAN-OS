import os
import sys
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from routing.gateway import InferenceGateway

class MainCoder:
    def __init__(self, project_id: str = "default"):
        self.project_id = project_id
        self.workspace_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), f"../../../staging/projects/{project_id}/workspace")
        )
        os.makedirs(self.workspace_dir, exist_ok=True)

    def write_module(self, project_blueprint: dict, node: dict, external_feedback: str = None, attempt: int = 1) -> str:
        filename = node.get("filename")
        print(f"[CODER] 👨‍💻 Writing atomic logic for node: {filename}...")

        # 1. Read the Hollow File skeleton
        file_path = os.path.join(self.workspace_dir, filename)
        hollow_code = ""
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                hollow_code = f.read()

        # 2. The Atomic Prompt
        system_prompt = (
            "You are the DEAN-OS Atomic Implementation Engine. "
            "You will receive a 'Hollow' Python file and must fill in the logic. "
            "CRITICAL RULES: "
            "1. Output ONLY raw, executable Python code. "
            "2. DO NOT use markdown formatting. NO triple backticks (```). "
            "3. DO NOT write any conversational text before or after the code. "
            "If you output anything other than pure Python code, the system will crash."
        )

        user_prompt = (
            f"# PURPOSE: {node.get('purpose')}\n"
            f"# REQUIRED SIGNATURES: {node.get('signatures')}\n\n"
            f"{hollow_code}"
        )

        if external_feedback:
            print(f"[CODER] ⚠️ Processing QA feedback from previous failure...")
            user_prompt = f"CRITICAL ERROR IN PREVIOUS ATTEMPT:\n{external_feedback}\n\nFix the logic and rewrite the module.\n\n" + user_prompt

        try:
            gateway = InferenceGateway()
            # [FIX] Force routing to OpenRouter 32B
            response = gateway.generate(
                system=system_prompt,
                prompt=user_prompt,
                task_type="CODE_GEN",
                attempt=attempt
            )
            raw_output = response['response'].strip()

            # 3. Scrub and save
            compiled_code = self._compile_code(raw_output)
            if compiled_code:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(compiled_code)
                print(f"[CODER] ✅ Atomic code injected into {filename}.")
                return file_path
            else:
                raise ValueError("Could not extract Python code from LLM output.")

        except Exception as e:
            print(f"[CODER ❌] Fatal Error: {e}")
            return None

    def _compile_code(self, text: str) -> str:
        # We asked for pure Python, so we just strip any accidental whitespace
        # and assume the LLM followed instructions.
        return text.strip()
