1. VISION AND PURPOSE
The Telemetry system is the "Nervous System" of Project DAEN. It provides real-time visibility into the health of your hardware and the logic of your agents. Without Telemetry, the system is a "black box"; with it, you have the data needed to prevent crashes, debug hallucinations, and optimize performance.

The goal is to provide Observability, which answers why a system is behaving a certain way, rather than just Monitoring, which only tells you if it is working.

2. HARDWARE TELEMETRY (THE SENTINEL)
This layer is managed by the Rust-based Resource Governor. It talks directly to the OS to ensure DAEN doesn't exceed the machine's physical limits.

A. RESOURCE METRICS
CPU LOAD: Tracks per-core utilization. If the "User Activity" (e.g., gaming or video editing) spikes, the system automatically throttles background agent tasks.

RAM PRESSURE: Monitors total system memory usage.

Threshold: 85% = Warning (Pause new tasks).

Threshold: 92% = Critical (Emergency Kill of lowest-priority agent).

VRAM (GPU) UTILIZATION: - Monitors VRAM usage specifically for LLM inference.

Checks for "Fragmentation" (where memory is available but scattered, causing model load failures).

B. THERMAL AND POWER
TEMPERATURE: Monitors CPU/GPU heat. If the system hits a "Thermal Ceiling," DAEN will insert "Cool-down Pauses" between agent loops.

POWER DRAW: Tracks energy consumption to help you understand the cost-to-performance ratio of your local models.

3. AGENTIC TELEMETRY (THE LOGIC TRACE)
This layer tracks how the AI agents are "thinking" and communicating. Every message sent through the Valkyrie-Link (Message Bus) is recorded.

A. THE KNOWLEDGE TRACE (DATA LINEAGE)
Every response generated must be logged with its origin marker:

[TRUTH_SOURCE]: The manual or doc used.

[DREAM_HYPOTHESIS]: The experimental idea.

[LEARNED_HISTORY]: The verified successful pattern.
Why: This allows you to audit the "Reasoning Path" of a failed project.

B. LATENCY AND TOKEN USAGE
TIME-TO-FIRST-TOKEN (TTFT): How fast the AI starts talking.

TOKENS PER SECOND (TPS): The actual speed of the local model.

CONTEXT PRESSURE: Monitors how "full" the AI's memory is (0%–100%). At 85%, the system triggers a Context Flush to prevent hallucination.

C. COGNITIVE FAULTS
HALLUCINATION EVENTS: Logged when the Hallucination Guard detects an agent inventing non-existent code.

SANDBOX FAILURES: Logs the specific error (SyntaxError, AttributeError) encountered during testing in the Oubliette-Lab.

4. THE TELEMETRY DASHBOARD (THE HUD)
The UI translates these raw numbers into a "Senior" level dashboard:

STATUS LIGHTS: Green (Optimal), Yellow (Resource Contention), Red (Immediate Shutdown Required).

THE AGENT GRAPH: A visual map showing which agents are talking to each other and who is currently "holding" the most system resources.

TRACE SEARCH: A search bar to look up past "Dream Sessions" and see why they passed or failed.

5. HARDWARE VALIDATION (THE PRE-FLIGHT CHECK)
Before the system even starts, the Telemetry service runs a "Pre-Flight" scan:

OS COMPATIBILITY: Checks for Linux (cgroups v2) or macOS/Windows equivalents.

GPU CAPABILITY: Detects NVIDIA/AMD/Apple Silicon and checks total VRAM.

STORAGE SPEED: Checks if the SSD is fast enough for the RAG Vault (Mnemosyne).

VERSION CHECK: Ensures all sub-projects (Aethelgard, Valkyrie, etc.) are at the correct version.

6. FUTURE SCALING: MULTI-NODE TELEMETRY
In future iterations involving multiple servers/users:

DISTRIBUTED LOGGING: Logs from different machines will be centralized into a single "Master Dashboard."

WORKLOAD REBALANCING: If Machine A has high heat but Machine B is cold, the Switchboard will automatically move the "Dreaming" loop to Machine B.