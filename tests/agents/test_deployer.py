import sys
import os

sys.path.append(os.path.abspath("services-python/sycophant"))
from agents.deployer import Deployer

def run_test():
    deployer = Deployer()

    # Target the file the Coder created earlier
    target_file = "csv_utils.py"

    print("Initiating Deployment Agent...")
    prod_path = deployer.deploy_module(filename=target_file)

    if prod_path and os.path.exists(prod_path):
        print(f"\n[VERIFIED] File successfully deployed to: {prod_path}")
    else:
        print("\n[FAILED] Deployer could not migrate the file.")

if __name__ == "__main__":
    run_test()
