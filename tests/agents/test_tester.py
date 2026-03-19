import sys
import os

# Point Python to the sycophant service so it can find the agents folder
sys.path.append(os.path.abspath("services-python/sycophant"))

from agents.tester import Tester

def run_test():
    tester = Tester(model_name="llama3.1:latest")

    # Target the file the Coder just created
    target_file = "csv_utils.py"

    print("Initiating Tester Agent...")
    file_path = tester.write_tests(filename=target_file)

    if file_path and os.path.exists(file_path):
        print(f"\n[VERIFIED] Test file successfully created at: {file_path}")
        print("\n--- File Contents ---")
        with open(file_path, "r") as f:
            print(f.read())
        print("---------------------")
    else:
        print("\n[FAILED] Tester did not generate or save the test file.")

if __name__ == "__main__":
    run_test()
