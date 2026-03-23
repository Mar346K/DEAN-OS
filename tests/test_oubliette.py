import pytest
from fastapi.testclient import TestClient
import valkyrie_crypto
import sys
import os

# Wire up the path so we can import the Oubliette app directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../services-python/oubliette')))
from app import app, INTERNAL_SECRET

client = TestClient(app)

def test_run_code_unauthorized():
    """Zero-Trust: Ensure missing token fails."""
    response = client.post("/run", json={"code": "print('hello')"})
    assert response.status_code == 401

def test_sandbox_isolation():
    """Ensure the sandbox executes code safely using the correct JSON payload."""
    token = valkyrie_crypto.forge_token("test-agent", "admin", INTERNAL_SECRET)
    headers = {"Authorization": f"Bearer {token}"}

    # This tries to look at the current directory.
    malicious_code = "import os; print(os.listdir('.'))"

    response = client.post("/run", json={"code": malicious_code}, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "output" in data

    # We want to ensure it doesn't see DEAN-OS host files (like daenctl.py)
    assert "daenctl.py" not in data["output"]
