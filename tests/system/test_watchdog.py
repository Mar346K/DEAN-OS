import pytest
from unittest.mock import patch
import requests
import sys
import os

sys.path.append(os.path.abspath("services-python/sycophant"))
from telemetry.watchdog import SystemWatchdog

@patch('telemetry.watchdog.requests.post')
@patch('telemetry.watchdog.requests.get')
def test_watchdog_all_healthy(mock_get, mock_post):
    """Happy Path: All services respond instantly."""
    guard = SystemWatchdog()
    # Should complete silently without raising SystemExit
    guard.run_preflight_check()
    assert mock_get.call_count == 2  # Ollama & Aethelgard
    assert mock_post.call_count == 1 # Oubliette

@patch('telemetry.watchdog.requests.get')
def test_watchdog_infrastructure_offline(mock_get):
    """Catastrophe Path: Ollama or Governor is offline."""
    # Force requests.get to raise a connection error
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection Refused")

    guard = SystemWatchdog()

    # Catch the sys.exit(1) to prove the watchdog halts the system
    with pytest.raises(SystemExit) as exc_info:
        guard.run_preflight_check()

    assert exc_info.value.code == 1
