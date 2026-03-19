import os
import shutil

class Deployer:
    def __init__(self):
        # The AI's messy sandbox
        self.staging_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../staging/workspace"))
        # The pristine production folder
        self.prod_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../workspace"))

        # Ensure production directory exists
        os.makedirs(self.prod_dir, exist_ok=True)

    def deploy_module(self, filename: str) -> str:
        print(f"[DEPLOYER] Migrating validated module '{filename}' to production workspace...")

        source_path = os.path.join(self.staging_dir, filename)
        target_path = os.path.join(self.prod_dir, filename)

        if not os.path.exists(source_path):
            print(f"[DEPLOYER ERROR] Source file {filename} not found in staging.")
            return None

        try:
            # [FIX] Ensure production subdirectories exist before copying
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # We use copy2 to preserve the original file metadata (creation times, etc.)
            shutil.copy2(source_path, target_path)
            print(f"[DEPLOYER SUCCESS] '{filename}' is now live in production.")
            return target_path
        except Exception as e:
            print(f"[DEPLOYER ERROR] Failed to deploy {filename}: {e}")
            return None
