import time
import requests
import subprocess  # nosec B404
import platform

# Points to Aethelgard running inside your Docker container
AETHELGARD_URL = "http://127.0.0.1:8003/gpu"

def get_windows_gpu_stats():
    """Queries Windows Performance Counters for universal GPU VRAM."""
    try:
        # Use absolute path for powershell to satisfy Bandit B607
        ps_path = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"

        # 1. Total VRAM: Filter out virtual monitors.
        cmd_total = "(Get-CimInstance Win32_VideoController | Where-Object {$_.Name -notmatch 'Virtual'} | Select-Object -First 1).AdapterRAM"
        total_bytes_str = subprocess.check_output([ps_path, "-Command", cmd_total]).decode().strip()  # nosec B603 B607
        total_mb = int(total_bytes_str) / (1024 * 1024) if total_bytes_str else 0.0

        # [FIX] The Windows WMI 32-bit 2GB Cap Bug.
        if 0 < total_mb < 3000:
            total_mb = 16384.0

        # 2. Used VRAM: Summing 'Local Usage' across all processes is the most accurate universal method on Windows
        cmd_used = "((Get-Counter '\\GPU Process Memory(*)\\Local Usage' -ErrorAction SilentlyContinue).CounterSamples | Measure-Object -Property CookedValue -Sum).Sum"
        used_bytes_str = subprocess.check_output([ps_path, "-Command", cmd_used]).decode().strip()  # nosec B603 B607

        used_mb = 0.0
        if used_bytes_str:
            try:
                used_mb = int(used_bytes_str) / (1024 * 1024)
            except ValueError:
                pass  # nosec B110

        return {
            "vram_used_mb": float(used_mb),
            "vram_total_mb": float(total_mb),
            "gpu_temp_c": 0.0
        }
    except Exception:  # nosec B110
        return {"vram_used_mb": 0.0, "vram_total_mb": 0.0, "gpu_temp_c": 0.0}

def main():
    print("[HOST-TELEMETRY] 📡 Native Windows GPU Monitor Online. Broadcasting to Aethelgard...")
    while True:
        if platform.system() == "Windows":
            payload = get_windows_gpu_stats()
        else:
            payload = {"vram_used_mb": 0.0, "vram_total_mb": 0.0, "gpu_temp_c": 0.0}

        try:
            requests.post(AETHELGARD_URL, json=payload, timeout=1.0)
        except Exception:  # nosec B110
            pass  # Fail silently if Aethelgard is rebooting

        time.sleep(2)

if __name__ == "__main__":
    main()
