import os
import sys
import json
from unittest.mock import patch

# Wire up the path to the Sycophant service
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services-python/sycophant")))
from agents.coder import MainCoder

def test_markdown_scrubber_removes_fences(tmp_path):
    """
    Verifies that the MainCoder's precision scrubber successfully strips
    markdown code fences from the LLM's raw output before saving to disk.
    """
    # 1. Initialize the Coder and safely redirect its output to Pytest's temp directory
    coder = MainCoder()
    coder.workspace_dir = str(tmp_path)

    # 2. Setup mock data for the Architect's blueprint
    mock_blueprint = {"project_name": "ScrubberTest"}
    target_file = {
        "filename": "dirty_code.py",
        "purpose": "Test markdown stripping",
        "signatures": ["def clean_me():"]
    }

    # 3. Construct the simulated LLM response safely to bypass UI parsers
    # Using concatenation of chr(96) to absolutely guarantee no literal triple ticks exist in this file
    tick = chr(96)
    triple_tick = tick + tick + tick

    # Simulates an LLM incorrectly returning the fenced python block
    dirty_python_string = f"{triple_tick}python\ndef clean_me():\n    pass\n{triple_tick}"
    mock_response_json = json.dumps({"code": dirty_python_string})

    # 4. Patch the InferenceGateway to return our dirty string
    with patch.object(coder.gateway, 'generate') as mock_generate:
        mock_generate.return_value = {"response": mock_response_json}

        # 5. Execute the coder
        output_path = coder.write_module(mock_blueprint, target_file)

    # 6. Assertions: File creation and cleanup verification
    assert output_path is not None, "Coder failed to return a valid file path."
    assert os.path.exists(output_path), "Coder failed to write the file to disk."

    with open(output_path, "r", encoding="utf-8") as f:
        cleaned_code = f.read()

    # The markdown fences and 'python' identifier MUST be gone
    assert triple_tick not in cleaned_code, "Failed to strip the markdown backticks!"
    assert not cleaned_code.startswith("python"), "Failed to strip the 'python' language identifier!"

    # The actual python code MUST remain intact
    assert "def clean_me():" in cleaned_code, "Accidentally stripped the actual code signature."
    assert "pass" in cleaned_code, "Accidentally stripped the function body."
