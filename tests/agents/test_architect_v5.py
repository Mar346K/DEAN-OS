import sys
import os
import json

sys.path.append(os.path.abspath("services-python/sycophant"))
from agents.architect import Architect

def test_graph_architect():
    architect = Architect()

    intent = "Build a CLI application that converts Markdown files to HTML. It needs a main entry point, a file I/O utility module, and a core Markdown parser module."

    # Mocking what the Researcher would have found
    mock_context = "Use the 'markdown-it-py' library for parsing. Use standard 'argparse' for the CLI."

    print("--- INITIATING GRAPH-NATIVE ARCHITECT ---")
    blueprint = architect.draft_plan(intent, mock_context)

    if blueprint:
        print("\n--- RETURNED DAG BLUEPRINT ---")
        print(json.dumps(blueprint, indent=2))
        print("------------------------------")
    else:
        print("\n[FAILED] Blueprint generation failed.")

if __name__ == "__main__":
    test_graph_architect()
