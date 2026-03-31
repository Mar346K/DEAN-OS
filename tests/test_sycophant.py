import pytest
from unittest.mock import patch, AsyncMock, MagicMock, mock_open
import sys
import os

# Wire up the path to the Sycophant service
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../services-python/sycophant')))
from tasks import async_execute_assembly_line as execute_task

@pytest.mark.asyncio
@patch('orchestrator.httpx.AsyncClient')
@patch('orchestrator.ollama.generate')
async def test_execute_task_self_healing(mock_ollama, mock_async_client_class):
    """Test that the Orchestrator successfully retries when the Sandbox fails."""

    mock_client = AsyncMock()
    mock_async_client_class.return_value.__aenter__.return_value = mock_client

    mock_mnemosyne_resp = MagicMock()
    mock_mnemosyne_resp.status_code = 200
    mock_mnemosyne_resp.json.return_value = {"results": [{"text": "Mock context from memory."}]}

    mock_oubliette_fail = MagicMock()
    mock_oubliette_fail.status_code = 200
    mock_oubliette_fail.json.return_value = {"error": "Execution Error", "details": "ModuleNotFoundError"}

    mock_oubliette_success = MagicMock()
    mock_oubliette_success.status_code = 200
    mock_oubliette_success.json.return_value = {"output": "Hardware verified successfully!"}

    mock_client.post.side_effect = [
        mock_mnemosyne_resp,
        mock_oubliette_fail,
        mock_oubliette_success
    ]

    mock_ollama.return_value = {"response": "print('Mock code execution')"}

    result = await execute_task("Check the hardware.")

    assert result == {"output": "Hardware verified successfully!"}
    assert mock_ollama.call_count == 2
    assert mock_client.post.call_count == 3

@pytest.mark.asyncio
@patch('orchestrator.httpx.AsyncClient')
@patch('orchestrator.ollama.generate')
@patch('builtins.open', new_callable=mock_open)
@patch('orchestrator.os.makedirs')
async def test_execute_task_tool_request(mock_makedirs, mock_file, mock_ollama, mock_async_client_class):
    """Test that the Orchestrator safely intercepts JSON tool requests and logs them."""

    mock_client = AsyncMock()
    mock_async_client_class.return_value.__aenter__.return_value = mock_client

    mock_mnemosyne_resp = MagicMock()
    mock_mnemosyne_resp.status_code = 200
    mock_mnemosyne_resp.json.return_value = {"results": [{"text": "Mock context."}]}

    # We only expect 1 POST request (to Mnemosyne). The Sandbox should NEVER be called.
    mock_client.post.return_value = mock_mnemosyne_resp

    # Force the LLM to output the quarantine request format
    mock_ollama.return_value = {"response": '{"tool_request": "beautifulsoup4"}'}

    result = await execute_task("Scrape a site.")

    # 1. Verify the Brain aborted execution and returned the correct status
    assert result == {"status": "Quarantine Request Logged", "tool": "beautifulsoup4"}

    # 2. Verify the Sandbox was never called
    assert mock_client.post.call_count == 1

    # 3. Verify the tool was written to the file
    mock_file.assert_called_once()
    mock_file().write.assert_called_with("beautifulsoup4\n")
