import ollama
import json

class Architect:
    def __init__(self, model_name="llama3.1:latest"):
        self.model_name = model_name

    def draft_plan(self, user_intent: str, context: str = "") -> dict:
        print(f"[ARCHITECT] Drafting blueprint for: '{user_intent}'...")

        system_prompt = (
            "You are the DEAN-OS Lead Architect. Your job is to break down a user's request "
            "into a modular Python project structure.\n\n"
            "CRITICAL RULES:\n"
            "1. DO NOT write implementation code. No logic inside functions.\n"
            "2. Ensure the design is modular (Single Responsibility Principle).\n"
            "3. Output ONLY a valid JSON object. No markdown formatting, no conversational text.\n\n"
            "JSON SCHEMA:\n"
            "{\n"
            "  \"project_name\": \"string\",\n"
            "  \"files\": [\n"
            "    {\n"
            "      \"filename\": \"string (e.g., main.py)\",\n"
            "      \"purpose\": \"string (What this file does)\",\n"
            "      \"signatures\": [\"def func1(a: int) -> bool:\", \"class Name:\"]\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = f"User Intent: {user_intent}\n\nTechnical Context:\n{context}"

        try:
            # format="json" forces Ollama to strictly adhere to the JSON structure
            response = ollama.generate(
                model=self.model_name,
                system=system_prompt,
                prompt=user_prompt,
                format="json"
            )

            blueprint = json.loads(response['response'])
            return blueprint

        except json.JSONDecodeError as e:
            print(f"[ARCHITECT ERROR] Failed to parse JSON. Model hallucinated text: {e}")
            return None
        except Exception as e:
            print(f"[ARCHITECT ERROR] Inference failed: {e}")
            return None
