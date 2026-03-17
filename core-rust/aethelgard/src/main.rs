use sysinfo::{Pid, System};
use std::fs;
use std::thread;
use std::time::Duration;
use gfxinfo::active_gpu;

fn main() {
    println!("[SENTINEL] Booting Hardware Validation Loop...");

    let mut sys = System::new_all();

    // Safely unwrap the Result into an Option. Fails gracefully if no GPU is found.
    let gpu_option = active_gpu().ok();

    if let Some(ref gpu) = gpu_option {
        println!("[SENTINEL] Detected GPU: {} {}", gpu.vendor(), gpu.model());
    } else {
        println!("[WARNING] Failed to initialize gfxinfo. GPU telemetry disabled.");
    }

    loop {
        // --- 1. CPU & RAM TELEMETRY ---
        sys.refresh_memory();
        sys.refresh_cpu();

        let total_mem = sys.total_memory();
        let used_mem = sys.used_memory();
        let ram_usage = (used_mem as f64 / total_mem as f64) * 100.0;

        if ram_usage > 92.0 {
            println!("\n[CRITICAL] RAM Pressure at {:.2}%. Triggering OOM Protection...", ram_usage);
            enforce_oom_protection(&mut sys);
        } else {
            print!("\r[OK] RAM: {:.2}% | ", ram_usage);
        }

        // --- 2. GPU TELEMETRY ---
        // Only attempt to read VRAM if the GPU was successfully initialized
        if let Some(ref gpu) = gpu_option {
            let info = gpu.info();
            let total_vram = info.total_vram() as f64;

            if total_vram > 0.0 {
                let vram_usage = (info.used_vram() as f64 / total_vram) * 100.0;
                let temp = info.temperature() / 1000;
                print!("VRAM: {:.2}% | GPU Temp: {}°C", vram_usage, temp);
            } else {
                print!("VRAM: N/A | GPU Temp: N/A");
            }
        }

        use std::io::{self, Write};
        io::stdout().flush().unwrap();

        thread::sleep(Duration::from_secs(1));
    }
}

fn enforce_oom_protection(sys: &mut System) {
    let pid_file = "../../daen-pids.json";

    let data = match fs::read_to_string(pid_file) {
        Ok(content) => content,
        Err(_) => {
            println!("\n[WARNING] No daen-pids.json found. Cannot terminate agents.");
            return;
        }
    };

    let pids: Vec<usize> = serde_json::from_str(&data).unwrap_or_default();

    for pid_val in pids {
        let target_pid = Pid::from(pid_val);
        sys.refresh_processes();

        if let Some(process) = sys.process(target_pid) {
            println!("\n[EXECUTE] Terminating PID: {}", pid_val);
            process.kill();
        }
    }
}
