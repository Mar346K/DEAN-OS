import os
import sys
import subprocess # nosec B404
import re

# Use absolute paths so this script can be run from anywhere
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
QUEUE_FILE = os.path.join(BASE_DIR, "staging", "quarantine_queue.txt")
DOCKERFILE_PATH = os.path.join(BASE_DIR, "infrastructure", "containers", "sandbox.Dockerfile")

# A simple allowlist for now. In a production environment,
# this would ping a vulnerability database (like PyPI or Snyk).
APPROVED_LIBRARIES = ["beautifulsoup4", "requests", "numpy", "pandas", "psutil"]

def scan_package(package_name: str) -> bool:
    """Security Gate: Ensure the requested package is safe to install."""
    # Normalize to lowercase for comparison
    pkg_lower = package_name.lower()

    # Map common naming hallucinations to actual PyPI names
    mapping = {
        "beautifulsoup": "beautifulsoup4",
        "bs4": "beautifulsoup4"
    }
    target = mapping.get(pkg_lower, pkg_lower)

    # Clean the string
    clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '', target)

    if clean_name in [lib.lower() for lib in APPROVED_LIBRARIES]:
        return True

    print(f"[FORGE-SECURITY] Rejected: '{package_name}' not in approved list.")
    return False

def upgrade_sandbox(package_name: str):
    """Rewrite the Dockerfile and rebuild the container."""
    print(f"\n[FORGE] Upgrading Sandbox with: {package_name}")

    if not os.path.exists(DOCKERFILE_PATH):
        print(f"[FORGE] ERROR: Dockerfile not found at {DOCKERFILE_PATH}")
        return False

    # 1. Read the existing Dockerfile
    with open(DOCKERFILE_PATH, "r") as f:
        lines = f.readlines()

    if not lines:
        print("[FORGE] ERROR: Dockerfile is empty before editing. Aborting to prevent corruption.")
        return False

    # 2. Update lines
    updated = False
    new_lines = []
    for line in lines:
        if line.startswith("RUN pip install") and package_name not in line:
            new_lines.append(line.strip() + f" {package_name}\n")
            updated = True
        else:
            new_lines.append(line)

    # Failsafe: If no pip line found, append one
    if not updated and not any(package_name in l for l in lines):
        new_lines.append(f"RUN pip install {package_name}\n")
        updated = True

    # 3. Write back ONLY if we have content
    if updated and len(new_lines) > 0:
        with open(DOCKERFILE_PATH, "w") as f:
            f.writelines(new_lines)
    else:
        print(f"[FORGE] No changes needed or logic failed. Length: {len(new_lines)}")

    # 4. Rebuild
    print("[FORGE] Rebuilding daen-agent-sandbox image...")
    try:
        # Use absolute path for Dockerfile to be 100% sure
        subprocess.run(
            ["docker", "build", "-t", "daen-agent-sandbox", "-f", DOCKERFILE_PATH, "."],
            check=True,
            cwd=BASE_DIR
        ) # nosec B603 B607
        print(f"[FORGE] SUCCESS! Sandbox upgraded.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FORGE] ERROR: Docker build failed: {e}")
        return False

def process_queue():
    """Read the quarantine queue and process requests."""
    if not os.path.exists(QUEUE_FILE):
        print("[FORGE] Queue is empty. Nothing to process.")
        return

    print("[FORGE] Checking Quarantine Queue...")
    with open(QUEUE_FILE, "r") as f:
        packages = f.readlines()

    for pkg in packages:
        pkg = pkg.strip()
        if not pkg: continue

        print(f"[FORGE] Evaluating request for: '{pkg}'")
        if scan_package(pkg):
            if upgrade_sandbox(pkg):
                print(f"[FORGE] '{pkg}' approved and installed.")
        else:
            print(f"[FORGE] '{pkg}' failed security audit. Ignored.")

    # Clear the queue after processing
    with open(QUEUE_FILE, "w") as f:
        f.write("")
    print("[FORGE] Queue cleared.")

if __name__ == "__main__":
    process_queue()
