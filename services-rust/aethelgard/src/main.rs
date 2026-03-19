use axum::{routing::{get, post}, Json, Router};
use gfxinfo::active_gpu;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use sysinfo::System;
use tokio::net::TcpListener;

// --- Phase 13: Graph-Theory Deadlock Structs ---
#[derive(Deserialize)]
struct TraceRequest {
    trace_id: String,
    source_agent: String,
    target_agent: String,
}

#[derive(Serialize)]
struct TraceResponse {
    status: String,
    message: String,
}

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

// [UPGRADE] AppState now holds the active DAG of agent conversations
struct AppState {
    sys: Mutex<System>,
    // trace_id -> Vec of agent names (the path of execution)
    active_traces: Mutex<HashMap<String, Vec<String>>>,
}

#[tokio::main]
async fn main() {
    println!("[AETHELGARD] Forging the Shield...");

    let mut sys = System::new_all();
    sys.refresh_all();

    let shared_state = Arc::new(AppState {
        sys: Mutex::new(sys),
        active_traces: Mutex::new(HashMap::new()),
    });

    let app = Router::new()
        .route("/metrics", get(get_metrics))
        .route("/trace", post(record_trace)) // [NEW] The Deadlock API
        .with_state(shared_state);

    let listener = TcpListener::bind("127.0.0.1:8003").await.unwrap();
    println!("[AETHELGARD] Online. Guarding Hardware & Monitoring DAG on http://127.0.0.1:8003");

    axum::serve(listener, app).await.unwrap();
}

// --- Phase 13: The DAG Deadlock Breaker ---
async fn record_trace(
    axum::extract::State(state): axum::extract::State<Arc<AppState>>,
    Json(payload): Json<TraceRequest>,
) -> Json<TraceResponse> {
    let mut traces = state.active_traces.lock().unwrap();

    // Fetch the current path for this specific task trace
    let path = traces.entry(payload.trace_id.clone()).or_insert_with(Vec::new);

    // If this is a brand new task, log the source agent first
    if path.is_empty() {
        path.push(payload.source_agent.clone());
    }

    // Log the delegation target
    path.push(payload.target_agent.clone());

    // CYCLE DETECTION: How many times has this exact target agent been called in this trace?
    let occurrences = path.iter().filter(|&agent| agent == &payload.target_agent).count();

    // If an agent is visited more than 3 times in a single trace, it's an infinite loop.
    if occurrences > 3 {
        println!(
            "[AETHELGARD 🛑] DEADLOCK DETECTED! Trace '{}' is trapped in a circular loop involving '{}'.",
            payload.trace_id, payload.target_agent
        );

        // Purge the corrupted trace from memory
        traces.remove(&payload.trace_id);

        return Json(TraceResponse {
            status: "DEADLOCK_PREVENTED".to_string(),
            message: format!("Infinite delegation loop detected involving '{}'. Circuit broken.", payload.target_agent),
        });
    }

    println!(
        "[AETHELGARD 👁️] Trace '{}': {} -> {} (Hop: {})",
        payload.trace_id, payload.source_agent, payload.target_agent, path.len() - 1
    );

    Json(TraceResponse {
        status: "OK".to_string(),
        message: "Trace recorded. DAG is acyclic.".to_string(),
    })
}

// --- Original Hardware Governor ---
async fn get_metrics(
    axum::extract::State(state): axum::extract::State<Arc<AppState>>,
) -> Json<SystemMetrics> {
    let mut sys = state.sys.lock().unwrap();

    sys.refresh_cpu();
    sys.refresh_memory();

    let cpu_usage = sys.global_cpu_info().cpu_usage();
    let ram_used = sys.used_memory() / 1024 / 1024;
    let ram_total = sys.total_memory() / 1024 / 1024;
    let ram_percent = (ram_used as f32 / ram_total as f32) * 100.0;

    let mut vram_used = 0.0;
    let mut vram_total = 0.0;
    let mut vram_percent = 0.0;
    let mut gpu_temp = 0.0;

    if let Ok(gpu) = active_gpu() {
        let info = gpu.info();
        vram_total = info.total_vram() as f32 / 1024.0 / 1024.0;
        vram_used = info.used_vram() as f32 / 1024.0 / 1024.0;
        if vram_total > 0.0 { vram_percent = (vram_used / vram_total) * 100.0; }
        gpu_temp = info.temperature() as f32 / 1000.0;
    }

    let status = if ram_percent > 85.0 || vram_percent > 90.0 {
        "CRITICAL".to_string()
    } else {
        "HEALTHY".to_string()
    };

    Json(SystemMetrics {
        status, cpu_usage_percent: cpu_usage, ram_used_mb: ram_used, ram_total_mb: ram_total,
        ram_usage_percent: ram_percent, vram_used_mb: vram_used, vram_total_mb: vram_total,
        vram_usage_percent: vram_percent, gpu_temp_c: gpu_temp,
    })
}
