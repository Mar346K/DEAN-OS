import os
import json
import sys

# Wire up paths to our new domain folders
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.ast_mapper import ProjectMapper
from routing.gateway import InferenceGateway

class MainCoder:
    def __init__(self):
        self.workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../staging/workspace"))
        self.gateway = InferenceGateway()

    def write_module(self, project_blueprint: dict, target_file: dict, feedback: str = None, attempt: int = 1) -> str:
        filename = target_file.get("filename")
        print(f"[CODER] Writing implementation for: {filename}...")

        # [PHASE 14] Generate the live AST Map
        mapper = ProjectMapper(self.workspace_dir)
        ast_map = mapper.generate_map()

        code_schema = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The raw, executable Python code. Absolutely no markdown formatting or conversational text."
                }
            },
            "required": ["code"]
        }

        system_prompt = (
            "You are the DEAN-OS Lead Python Developer. "
            "You must output YOUR ENTIRE RESPONSE as a valid JSON object matching the requested schema. "
            "1. Implement the exact function signatures requested.\n"
            "2. Include necessary imports.\n"
            "3. Write clean, production-ready code with basic docstrings.\n"
            "4. NEVER use interactive `input()` at the module root level."
        )

        user_prompt = (
            f"GLOBAL EXPORT MAP (Current state of the project):\n{ast_map}\n\n"
            f"PROJECT BLUEPRINT:\n{project_blueprint}\n\n"
            f"YOUR TASK:\nWrite the complete implementation for the file: {filename}\n"
            f"Purpose: {target_file.get('purpose')}\n"
            f"Required Signatures: {target_file.get('signatures')}\n"
        )

        if feedback:
            print(f"[CODER] ⚠️ Processing feedback from previous failure...")
            user_prompt += f"\n\nCRITICAL ERROR FEEDBACK:\nYour previous attempt failed with the following errors:\n{feedback}\n\nFix these errors in the new code.\n"

        try:
            # [PHASE 14.2] Route through the Smart-Tier Gateway
            response = self.gateway.generate(
                system=system_prompt,
                prompt=user_prompt,
                format_schema=code_schema,
                attempt=attempt
            )

            result_json = json.loads(response['response'])
            raw_code = result_json.get("code", "")

            file_path = os.path.join(self.workspace_dir, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(raw_code)

            print(f"[CODER SUCCESS] Saved {filename} to workspace.")
            return file_path

        except json.JSONDecodeError as e:
            print(f"[CODER ERROR] FSM Violation - Invalid JSON returned: {e}")
            return None
        except Exception as e:
            print(f"[CODER ERROR] Failed to write module {filename}: {e}")
            return None
