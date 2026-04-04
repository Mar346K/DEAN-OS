import sys
import os

sys.path.append(os.path.abspath("services-python/sycophant"))
from agents.researcher import CloudResearcher

def test_cloud_research():
    researcher = CloudResearcher()

    intent = "What is the newest, best way to hash passwords in Python in 2026? Give me the exact library and a code snippet."

    print("--- INITIATING CLOUD RESEARCH ---")
    brief = researcher.research_task(intent)

    print("\n--- RETURNED TECHNICAL BRIEF ---")
    print(brief)
    print("--------------------------------")

if __name__ == "__main__":
    test_cloud_research()
