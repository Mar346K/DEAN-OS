import json
import os
import requests
import valkyrie_crypto

class Architect:
    """
    The Master Planner of DEAN-OS v5.0.
    Uses Gemini 2.5 Flash to convert a user's intent and technical research
    into a strict Directed Acyclic Graph (DAG) of Python contracts.
    """
    def __init__(self, project_id: str = "default"):
        self.project_id = project_id
        self.secret = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

    def draft_plan(self, user_intent: str, context: str = "") -> dict:
        print(f"[ARCHITECT] 🏗️ Drafting Graph-Native Blueprint for: '{user_intent}'")

        api_key = valkyrie_crypto.unseal_key("gemini", self.secret)
        if not api_key:
            print("[ARCHITECT ❌] CRITICAL: Gemini API key not found in the Vault.")
            return None

        # --- THE V5.0 GRAPH PROMPT ---
        system_instruction = (
            "You are the DEAN-OS Lead Architect. Your job is to design modular Python project structures.\n"
            "You MUST output your design as a Directed Acyclic Graph (DAG) in pure JSON format.\n\n"
            "CRITICAL RULES:\n"
            "1. DO NOT write implementation code. Only write strict function/class signatures (The Contract).\n"
            "2. Ensure Single Responsibility Principle. Break logic into distinct modules.\n"
            "3. Provide exactly ONE JSON object. No markdown fences, no conversational text.\n\n"
            "JSON SCHEMA REQUIREMENT:\n"
            "{\n"
            "  \"project_name\": \"string\",\n"
            "  \"nodes\": [\n"
            "    {\n"
            "      \"filename\": \"string (e.g., utils.py)\",\n"
            "      \"purpose\": \"string (What this module does)\",\n"
            "      \"signatures\": [\"def func_a(val: int) -> str:\", \"class Worker:\"]\n"
            "    }\n"
            "  ],\n"
            "  \"edges\": [\n"
            "    {\"source\": \"main.py\", \"target\": \"utils.py\"}\n"
            "  ]\n"
            "}"
        )

        user_prompt = f"USER INTENT: {user_intent}\n\nTECHNICAL RESEARCH CONTEXT:\n{context}\n\nOutput the JSON DAG:"

        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.0, # ZERO temperature for strict JSON determinism
                "response_mime_type": "application/json" # Force Gemini to output valid JSON
            }
        }

        try:
            response = requests.post(
                f"{self.api_url}?key={api_key}",
                json=payload,
                timeout=15.0
            )

            if response.status_code != 200:
                print(f"[ARCHITECT ❌] API Error: {response.status_code} - {response.text}")
                return None

            data = response.json()
            raw_output = data['candidates'][0]['content']['parts'][0]['text']

            blueprint = json.loads(raw_output)
            print(f"[ARCHITECT SUCCESS] ✅ DAG Blueprint generated with {len(blueprint.get('nodes', []))} nodes and {len(blueprint.get('edges', []))} edges.")
            return blueprint

        except json.JSONDecodeError as e:
            print(f"\n[ARCHITECT ERROR] Failed to parse JSON: {e}")
            print(f"--- RAW OUTPUT ---\n{raw_output}\n------------------")
            return None
        except Exception as e:
            print(f"[ARCHITECT ERROR] Fatal error during drafting: {e}")
            return None
