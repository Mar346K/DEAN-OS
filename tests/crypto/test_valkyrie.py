import valkyrie_crypto
import pytest

# [TRUTH_SOURCE]: Shared internal secret for validation tests
SECRET = "daen-internal-dev-secret-2026"  # nosec B105

def test_token_lifecycle():
    """Verify that we can forge and then immediately validate a token."""
    token = valkyrie_crypto.forge_token("scout-agent", "librarian", SECRET)
    assert token is not None  # nosec B101

    is_valid = valkyrie_crypto.validate_token(token, SECRET)
    assert is_valid is True  # nosec B101

def test_tamper_resistance():
    """Verify the Zero-Trust rule: Incorrect secrets must be rejected."""
    token = valkyrie_crypto.forge_token("scout-agent", "admin", SECRET)

    # Attempting to validate with the wrong key
    is_valid = valkyrie_crypto.validate_token(token, "hostile-secret-key")
    assert is_valid is False  # nosec B101

def test_malformed_input():
    """Verify that the Rust layer handles garbage strings without crashing."""
    assert valkyrie_crypto.validate_token("not.a.real.token", SECRET) is False  # nosec B101
