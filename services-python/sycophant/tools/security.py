import re

def redact_sensitive_info(text: str) -> str:
    """Removes API keys and secrets from log strings using regex."""
    if not isinstance(text, str):
        return text

    # Redact Gemini keys in URLs: ?key=AIza...
    scrubbed = re.sub(r'(key=)[a-zA-Z0-9_\-]+', r'\1[REDACTED_API_KEY]', text)

    # Redact standard AI keys: sk-...
    scrubbed = re.sub(r'sk-[a-zA-Z0-9]{20,}', '[REDACTED_API_KEY]', scrubbed)

    return scrubbed
