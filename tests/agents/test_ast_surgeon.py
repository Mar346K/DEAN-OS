import sys
import os

sys.path.append(os.path.abspath("services-python/sycophant"))
from tools.ast_surgeon import ASTSurgeon

def test_surgery():
    surgeon = ASTSurgeon()

    # 1. What the Architect Demanded
    target_contract = {
        "filename": "password_util.py",
        "signatures": ["def generate_secure_password(length: int, use_symbols: bool) -> str:"]
    }

    # 2. What the 14B LLM hallucinated (wrong name, wrong args, missing type hints)
    hallucinated_llm_code = """
import random
import string

def make_pass(l, syms):
    chars = string.ascii_letters
    if syms:
        chars += string.punctuation
    return ''.join(random.choice(chars) for _ in range(l))
"""

    print("--- BEFORE SURGERY ---")
    print(hallucinated_llm_code)

    print("\n--- INITIATING SURGERY ---")
    # 3. The Execution
    healed_code = surgeon.enforce_contract(hallucinated_llm_code, target_contract)

    print("\n--- AFTER SURGERY ---")
    print(healed_code)

if __name__ == "__main__":
    test_surgery()
