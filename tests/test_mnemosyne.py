import pytest
from fastapi.testclient import TestClient
import valkyrie_crypto
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../services-python/mnemosyne')))
from app import app, INTERNAL_SECRET

client = TestClient(app)

def test_search_memory_unauthorized():
    """Zero-Trust Check: Ensure requests without a Valkyrie token are rejected."""
    response = client.post("/search?query=test")
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing Authorization Token"}

def test_search_memory_invalid_token():
    """Zero-Trust Check: Ensure forged/fake tokens are caught."""
    headers = {"Authorization": "Bearer fake-malicious-token"}
    response = client.post("/search?query=test", headers=headers)
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid Token"}

def test_search_memory_success():
    """Ensure authorized agents can successfully retrieve context."""
    token = valkyrie_crypto.forge_token("test-agent", "tester", INTERNAL_SECRET)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/search?query=hardware", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    assert "DEAN-OS Hardware Documentation" in data["results"][0]["text"]
