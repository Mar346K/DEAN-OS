import valkyrie_crypto
import pytest

def test_dlp_scrubs_aws_keys():
    """Verify the Regex engine catches and redacts standard AWS Access Keys."""
    dirty_payload = "The system crashed. Here is the context: AKIAIOSFODNN7EXAMPLE. Please fix." # gitleaks:allow
    clean_payload = valkyrie_crypto.enforce_dlp_egress(dirty_payload)

    assert "AKIAIOSFODNN7EXAMPLE" not in clean_payload # gitleaks:allow
    assert "[REDACTED_AWS_KEY]" in clean_payload
    assert "The system crashed. Here is the context: [REDACTED_AWS_KEY]. Please fix." == clean_payload

def test_dlp_scrubs_jwt_tokens():
    """Verify the Regex engine destroys base64 JWTs."""
    # A standard mock JWT header.payload.signature
    dirty_payload = "My token is eyJhbGciOiJIUzI1NiIsInR5cCI.eyJzdWIiOiIxMjM0NTY3ODkwIiw.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c" # gitleaks:allow
    clean_payload = valkyrie_crypto.enforce_dlp_egress(dirty_payload)

    assert "eyJhbGci" not in clean_payload
    assert "[REDACTED_JWT_TOKEN]" in clean_payload

def test_dlp_scrubs_proprietary_secrets():
    """Verify exact-match redaction for internal DEAN-OS variables."""
    dirty_payload = "Connect to the database using HR_DB_PASSWORD and the nexus_risk_solana_key."
    clean_payload = valkyrie_crypto.enforce_dlp_egress(dirty_payload)

    assert "HR_DB_PASSWORD" not in clean_payload
    assert "nexus_risk_solana_key" not in clean_payload
    assert clean_payload.count("[REDACTED_PROPRIETARY_SECRET]") == 2

def test_dlp_ignores_clean_traffic():
    """Ensure standard prompts pass through the Air-Lock uncorrupted."""
    clean_prompt = "Write a python script to calculate the Fibonacci sequence."
    processed_prompt = valkyrie_crypto.enforce_dlp_egress(clean_prompt)

    assert processed_prompt == clean_prompt
