import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import sys
import os

# Wire up the path to the Sycophant service
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../services-python/sycophant')))
from orchestrator import execute_task

@pytest.mark.asyncio
@patch('orchestrator.httpx.AsyncClient')
@patch('orchestrator.ollama.generate')
async def test_execute_task_self_healing(mock_ollama, mock_async_client_class):
    """Test that the Orchestrator successfully retries when the Sandbox fails."""

    # 1. Intercept the HTTP Client
    mock_client = AsyncMock()
    mock_async_client_class.return_value.__aenter__.return_value = mock_client

    # --- Setup Fake HTTP Responses ---

    # Fake Call 1: Mnemosyne Context (Success)
    mock_mnemosyne_resp = MagicMock()
    mock_mnemosyne_resp.status_code = 200
    mock_mnemosyne_resp.json.return_value = {"results": [{"text": "Mock context from memory."}]}

    # Fake Call 2: Oubliette Execution (Simulate a Crash!)
    mock_oubliette_fail = MagicMock()
    mock_oubliette_fail.status_code = 200
    mock_oubliette_fail.json.return_value = {"error": "Execution Error", "details": "ModuleNotFoundError: No module named 'psutil'"}

    # Fake Call 3: Oubliette Execution (Simulate a Success on Retry)
    mock_oubliette_success = MagicMock()
    mock_oubliette_success.status_code = 200
    mock_oubliette_success.json.return_value = {"output": "Hardware verified successfully!"}

    # Map the fake responses to the order the Orchestrator will call them
    mock_client.post.side_effect = [
        mock_mnemosyne_resp,     # 1st POST to /search
        mock_oubliette_fail,     # 2nd POST to /run (Attempt 1)
        mock_oubliette_success   # 3rd POST to /run (Attempt 2)
    ]

    # 2. Intercept Ollama (The GPU)
    mock_ollama.return_value = {"response": "print('Mock code execution')"}

    # 3. Fire the Orchestrator
    result = await execute_task("Check the hardware.")

    # 4. Verify the Agentic Logic
    assert result == {"output": "Hardware verified successfully!"}
    assert mock_ollama.call_count == 2     # Proof: It rewrote the code!
    assert mock_client.post.call_count == 3 # Proof: 1 Memory search + 2 Sandbox runs
