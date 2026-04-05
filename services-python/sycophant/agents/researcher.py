import os
import requests
import valkyrie_crypto
from sycophant.tools.security import redact_sensitive_info

class CloudResearcher:
    """
    The "Brain" of DEAN-OS v5.0.
    Leverages Gemini 1.5 Flash and Google Search to perform sprawling internet
    research and condense it into a dense technical brief for the local GPU.
    """
    def __init__(self):
        self.secret = os.getenv("DAEN_INTERNAL_SECRET", "daen-internal-dev-secret-2026")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

    def research_task(self, user_intent: str) -> str:
        print(f"[RESEARCHER] 🌐 Linking to Google Labs for intent: '{user_intent}'")

        # 1. Unseal the API Key from the Rust Zero-Knowledge Vault
        api_key = valkyrie_crypto.unseal_key("gemini", self.secret)
        if not api_key:
            print("[RESEARCHER ❌] CRITICAL: Gemini API key not found or corrupted in the Vault.")
            return "ERROR: No external context available. Proceed with local knowledge."

        print("[RESEARCHER] 🔓 Vault unsealed. Querying global intelligence...")

        # 2. Construct the Payload with Search Grounding
        system_instruction = (
            "You are the DEAN-OS Lead Technical Researcher. "
            "Use Google Search to find the latest best practices, required libraries, and optimal architectural patterns for the user's request. "
            "Output a dense 'Technical Brief'. Include critical code snippets, library names, and security considerations. "
            "Do NOT write conversational filler. Your output is being fed directly into a local, isolated 14B parameter AI coder."
        )

        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": [{"text": f"Research this task and provide the blueprint: {user_intent}"}]}],
            "tools": [{"googleSearch": {}}], # <--- THIS ENABLES LIVE INTERNET ACCESS
            "generationConfig": {"temperature": 0.2}
        }

        try:
            # 3. Execute the Cloud API Call
            response = requests.post(
                f"{self.api_url}?key={api_key}",
                json=payload,
                timeout=30.0 # Research might take a few seconds
            )

            if response.status_code != 200:
                # SECURE LOGGING: Scrub the response text just in case it mirrors the URL
                safe_error_text = redact_sensitive_info(response.text)
                print(f"[RESEARCHER ❌] API Error: {response.status_code} - {safe_error_text}")
                return "ERROR: Cloud API rejected the request."

            data = response.json()

            # 4. Extract the text
            try:
                technical_brief = data['candidates'][0]['content']['parts'][0]['text']
                print(f"[RESEARCHER] ✅ Intelligence gathered ({len(technical_brief)} chars).")
                return technical_brief
            except (KeyError, IndexError):
                print("[RESEARCHER ❌] Unexpected API response format.")
                return "ERROR: Malformed Cloud Intelligence."

        except requests.exceptions.Timeout:
            print("[RESEARCHER 🛑] Connection to Google Labs timed out.")
            return "ERROR: Cloud API Timeout."
        except Exception as e:
            # SECURE LOGGING: Scrub the exception string
            safe_error = redact_sensitive_info(str(e))
            print(f"[RESEARCHER ❌] Fatal Error: {safe_error}")
            return f"ERROR: {safe_error}"
