import pytest
from unittest.mock import patch
import requests
import sys
import os

sys.path.append(os.path.abspath("services-python/sycophant"))
from agents.analyzer import Analyzer

@patch('agents.analyzer.requests.post')
@patch('agents.analyzer.valkyrie_crypto.forge_token', return_value="mock_secure_token")
def test_analyzer_infinite_loop_circuit_breaker(mock_forge, mock_post):
    """Catastrophe Path: The AI writes an infinite loop and Docker hangs."""

    # Force the Sandbox POST request to instantly time out
    mock_post.side_effect = requests.exceptions.Timeout("Read timed out")

    analyzer = Analyzer()
    report = analyzer.evaluate_code("test_fake_file.py")

    # Verify the Circuit Breaker caught the timeout and handled it securely
    assert report["status"] == "fail"
    assert report["type"] == "loud"
    assert "infinite loop" in report["logs"].lower()
    assert "Execution timed out" in report["logs"]
