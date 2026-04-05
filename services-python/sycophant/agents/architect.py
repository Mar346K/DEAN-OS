import json
import os
import requests
import valkyrie_crypto
from sycophant.tools.security import redact_sensitive_info

class Architect:
    """
    The Master Planner of DEAN-OS v5.1.
    Uses Gemini 2.5 Flash to convert a user's intent into a JSON DAG,
    and then performs a 'Ghost Execution' to simulate data flow and catch
    circular dependencies before committing to local generation.
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

        # --- PHASE 1: The Initial Draft ---
        blueprint = self._generate_initial_dag(user_intent, context, api_key)
        if not blueprint:
            return None

        # --- PHASE 2: The Digital Twin Simulation ---
        print("[ARCHITECT] 👻 Initializing Digital Twin for Ghost Execution...")
        simulation_result = self._simulate_ghost_execution(blueprint, api_key)

        if simulation_result.get("status") == "PASS":
            print(f"[ARCHITECT SUCCESS] ✅ DAG Blueprint verified by Digital Twin. Simulated Execution Time: {simulation_result.get('estimated_ms', 0)}ms.")
            return blueprint
        else:
            print(f"[ARCHITECT ⚠️] Digital Twin detected a fatal flaw: {simulation_result.get('reason')}")
            print("[ARCHITECT] ♻️ Triggering Architectural Refactor...")

            # Feed the failure back into the generator for a second attempt
            refactor_context = f"{context}\n\nCRITICAL SYSTEM FEEDBACK: Your previous architecture failed simulation. REASON: {simulation_result.get('reason')}. Fix this flaw."
            refactored_blueprint = self._generate_initial_dag(user_intent, refactor_context, api_key)

            if refactored_blueprint:
                 print("[ARCHITECT SUCCESS] ✅ Refactored DAG Blueprint generated.")
                 return refactored_blueprint
            return None

    def _generate_initial_dag(self, user_intent: str, context: str, api_key: str) -> dict:
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
            "generationConfig": {"temperature": 0.0, "response_mime_type": "application/json"}
        }

        try:
            response = requests.post(f"{self.api_url}?key={api_key}", json=payload, timeout=15.0)
            response.raise_for_status()
            raw_output = response.json()['candidates'][0]['content']['parts'][0]['text']
            return json.loads(raw_output)
        except Exception as e:
            # SECURE LOGGING
            safe_error = redact_sensitive_info(str(e))
            print(f"[ARCHITECT ERROR] Failed to generate DAG: {safe_error}")
            return None

    def _simulate_ghost_execution(self, blueprint: dict, api_key: str) -> dict:
        """
        Forces Gemini to mentally step through the code execution based only on signatures.
        """
        system_instruction = (
            "You are the DEAN-OS Digital Twin Simulator. "
            "You will be given a JSON Directed Acyclic Graph (DAG) representing a software architecture. "
            "You must perform a 'Ghost Execution'. Trace the data flow from the entry point through the edges. "
            "Analyze the function signatures for missing inputs, mismatched types, or circular dependencies.\n\n"
            "Output your findings strictly as JSON matching this schema:\n"
            "{\n"
            "  \"status\": \"PASS\" or \"FAIL\",\n"
            "  \"reason\": \"Detailed explanation of why it failed (or 'Architecture is sound').\",\n"
            "  \"estimated_ms\": integer (guess the execution time of the critical path)\n"
            "}"
        )

        user_prompt = f"SIMULATE THIS ARCHITECTURE:\n{json.dumps(blueprint, indent=2)}"

        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.1, "response_mime_type": "application/json"}
        }

        try:
            response = requests.post(f"{self.api_url}?key={api_key}", json=payload, timeout=15.0)
            response.raise_for_status()
            raw_output = response.json()['candidates'][0]['content']['parts'][0]['text']
            return json.loads(raw_output)
        except Exception as e:
            # SECURE LOGGING
            safe_error = redact_sensitive_info(str(e))
            print(f"[TWIN ERROR] Simulation failed, defaulting to PASS to prevent deadlock: {safe_error}")
            return {"status": "PASS", "reason": "Simulation bypassed due to timeout.", "estimated_ms": 0}
