use axum::{routing::get, Json, Router};
use gfxinfo::active_gpu;
use serde::Serialize;
use std::sync::{Arc, Mutex};
use sysinfo::System;
use tokio::net::TcpListener;

// Expanded data structure including the GPU
#[derive(Serialize)]
struct SystemMetrics {
    status: String,
    cpu_usage_percent: f32,
    ram_used_mb: u64,
    ram_total_mb: u64,
    ram_usage_percent: f32,
    vram_used_mb: f32,
    vram_total_mb: f32,
    vram_usage_percent: f32,
    gpu_temp_c: f32,
}

struct AppState {
    sys: Mutex<System>,
}

#[tokio::main]
async fn main() {
    println!("[AETHELGARD] Forging the Shield...");

    let mut sys = System::new_all();
    sys.refresh_all();

    let shared_state = Arc::new(AppState {
        sys: Mutex::new(sys),
    });

    let app = Router::new()
        .route("/metrics", get(get_metrics))
        .with_state(shared_state);

    let listener = TcpListener::bind("127.0.0.1:8003").await.unwrap();
    println!("[AETHELGARD] Online. Guarding CPU, RAM, and GPU on http://127.0.0.1:8003/metrics");

    axum::serve(listener, app).await.unwrap();
}

async fn get_metrics(
    axum::extract::State(state): axum::extract::State<Arc<AppState>>,
) -> Json<SystemMetrics> {
    let mut sys = state.sys.lock().unwrap();

    sys.refresh_cpu();
    sys.refresh_memory();

    // 1. CPU & RAM Calculation
    let cpu_usage = sys.global_cpu_info().cpu_usage();
    let ram_used = sys.used_memory() / 1024 / 1024;
    let ram_total = sys.total_memory() / 1024 / 1024;
    let ram_percent = (ram_used as f32 / ram_total as f32) * 100.0;

    // 2. GPU Calculation (Intel Arc)
    let mut vram_used = 0.0;
    let mut vram_total = 0.0;
    let mut vram_percent = 0.0;
    let mut gpu_temp = 0.0;

    // We fetch the GPU safely so if it fails, it doesn't crash the server
    if let Ok(gpu) = active_gpu() {
        let info = gpu.info();
        vram_total = info.total_vram() as f32 / 1024.0 / 1024.0;
        vram_used = info.used_vram() as f32 / 1024.0 / 1024.0;

        if vram_total > 0.0 {
            vram_percent = (vram_used / vram_total) * 100.0;
        }

        // gfxinfo returns temp in millidegrees Celsius
        gpu_temp = info.temperature() as f32 / 1000.0;
    }

    // 3. The Governor's Judgment
    let status = if ram_percent > 85.0 || vram_percent > 90.0 {
        "CRITICAL".to_string()
    } else {
        "HEALTHY".to_string()
    };

    Json(SystemMetrics {
        status,
        cpu_usage_percent: cpu_usage,
        ram_used_mb: ram_used,
        ram_total_mb: ram_total,
        ram_usage_percent: ram_percent,
        vram_used_mb: vram_used,
        vram_total_mb: vram_total,
        vram_usage_percent: vram_percent,
        gpu_temp_c: gpu_temp,
    })
}
