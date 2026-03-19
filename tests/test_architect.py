import json
import sys
import os

# Point Python to the sycophant service so it can find the agents folder
sys.path.append(os.path.abspath("services-python/sycophant"))

from agents.architect import Architect

def run_test():
    # Make sure you have llama3.1 pulled in Ollama!
    architect = Architect(model_name="llama3.1:latest")

    intent = "Build a modular terminal Blackjack game with CSV save states for player bankrolls."

    print("Initiating Architect Agent...")
    blueprint = architect.draft_plan(user_intent=intent)

    if blueprint:
        print("\n[SUCCESS] Blueprint Generated and Parsed:")
        print(json.dumps(blueprint, indent=2))
    else:
        print("\n[FAILED] Architect could not generate a valid blueprint.")

if __name__ == "__main__":
    run_test()
