import sys
import os

sys.path.append(os.path.abspath("services-python/sycophant"))
from agents.analyzer import Analyzer

def run_test():
    analyzer = Analyzer()

    # Target the test file the Tester agent just created
    target_file = "test_csv_utils.py"

    print("Initiating Analyzer Agent...")
    report = analyzer.evaluate_code(test_filename=target_file)

    print("\n--- ANALYZER REPORT ---")
    print(f"Status: {report['status'].upper()}")
    if report.get('type'):
        print(f"Failure Type: {report['type'].upper()}")
    print(f"\nRAW LOGS:\n{report['logs']}")
    print("-----------------------")

if __name__ == "__main__":
    run_test()
