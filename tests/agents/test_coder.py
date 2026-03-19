import sys
import os

# Point Python to the sycophant service so it can find the agents folder
sys.path.append(os.path.abspath("services-python/sycophant"))

from agents.coder import MainCoder

def run_test():
    coder = MainCoder(model_name="llama3.1:latest")

    # Mocking the blueprint output from the Architect
    mock_blueprint = {
        "project_name": "Blackjack"
    }

    # The specific file we want the Coder to build
    target_file = {
      "filename": "csv_utils.py",
      "purpose": "Handles CSV save states for player bankrolls, including loading and saving data.",
      "signatures": [
        "def load_bankroll(name: str) -> float",
        "def save_bankroll(name: str, amount: float)"
      ]
    }

    print("Initiating Main Coder Agent...")
    file_path = coder.write_module(project_blueprint=mock_blueprint, target_file=target_file)

    if file_path and os.path.exists(file_path):
        print(f"\n[VERIFIED] File successfully created at: {file_path}")
        print("\n--- File Contents ---")
        with open(file_path, "r") as f:
            print(f.read())
        print("---------------------")
    else:
        print("\n[FAILED] Coder did not generate or save the file.")

if __name__ == "__main__":
    run_test()
