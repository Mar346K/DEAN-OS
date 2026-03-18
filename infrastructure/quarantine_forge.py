import os
import sys
import subprocess # nosec B404
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
QUEUE_FILE = os.path.join(BASE_DIR, "staging", "quarantine_queue.txt")
DOCKERFILE_PATH = os.path.join(BASE_DIR, "infrastructure", "containers", "sandbox.Dockerfile")

# The normalized allowlist
APPROVED_LIBRARIES = ["beautifulsoup4", "requests", "numpy", "pandas", "psutil"]

def scan_package(package_name: str):
    """Normalize and audit requested packages."""
    pkg_lower = package_name.lower()

    # Translation Layer: Map common LLM naming errors to real packages
    translation_map = {
        "beautifulsoup": "beautifulsoup4",
        "beautifulsoup3": "beautifulsoup4",
        "bs4": "beautifulsoup4"
    }

    target = translation_map.get(pkg_lower, pkg_lower)

    # Final security check against allowlist
    if target in APPROVED_LIBRARIES:
        return target

    print(f"[FORGE-SECURITY] Rejected: '{package_name}' (Target: {target}) not in approved list.")
    return None

def upgrade_sandbox(package_name: str):
    """Rewrite Dockerfile and build."""
    print(f"\n[FORGE] Upgrading Sandbox with: {package_name}")

    with open(DOCKERFILE_PATH, "r") as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    for line in lines:
        if line.startswith("RUN pip install"):
            # Check if normalized name is already there
            if package_name in line:
                print(f"[FORGE] '{package_name}' already present. Skipping.")
                return True
            new_lines.append(line.strip() + f" {package_name}\n")
            updated = True
        else:
            new_lines.append(line)

    if updated:
        with open(DOCKERFILE_PATH, "w") as f:
            f.writelines(new_lines)

    print("[FORGE] Rebuilding daen-agent-sandbox...")
    try:
        subprocess.run(
            ["docker", "build", "-t", "daen-agent-sandbox", "-f", DOCKERFILE_PATH, "."],
            check=True, cwd=BASE_DIR
        ) # nosec B603 B607
        return True
    except Exception as e:
        print(f"[FORGE] Build Error: {e}")
        return False

def process_queue():
    if not os.path.exists(QUEUE_FILE): return

    with open(QUEUE_FILE, "r") as f:
        packages = list(set(f.read().splitlines())) # Deduplicate

    for pkg in packages:
        if not pkg: continue
        target_pkg = scan_package(pkg)
        if target_pkg:
            upgrade_sandbox(target_pkg)

    with open(QUEUE_FILE, "w") as f: f.write("")

if __name__ == "__main__":
    process_queue()
