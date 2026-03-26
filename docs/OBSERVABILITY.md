# OBSERVABILITY.md: The Glass-Box Hypervisor


## 1. Vision & Purpose


Multi-agent systems are notoriously difficult to debug because they often act as "black boxes." DEAN-OS provides 360-degree visibility into the hardware health and the logical "thought process" of the swarm. This ensures operational safety and high-speed diagnosis of agentic failures.


---


## 2. Hardware Telemetry: The Aethelgard Sentinel


Managed by a high-performance **Rust Governor**, this layer monitors the physical limits of the host machine to prevent AI-driven system crashes.


* **The VRAM Bridge:** A native Windows performance daemon that broadcasts real-time Intel Arc VRAM utilization through the Docker firewall.


* **Resource Pressure Management:**
  * **Warning (85% RAM):** System pauses new agent tasks.
  * **Critical (92% RAM):** Aethelgard executes a `SIGKILL` on the lowest-priority agent process to save the host OS.


* **Thermal Intelligence:** CPU/GPU thermal monitoring. If the machine hits a "Thermal Ceiling," the system inserts cool-down pauses between agent loops.


---


## 3. Distributed Tracing: The Nervous System


DEAN-OS utilizes **Distributed Tracing** to track requests as they hop across the microservice cluster.


* **Trace Context (W3C):** Every request is stamped with a unique `trace_id` that follows the logic from the React UI -> FastAPI -> Redis -> Celery Worker -> LLM.


* **The Waterfall Log:** The Mission Control dashboard displays a millisecond-accurate timeline of every agent "hop," allowing developers to identify latency bottlenecks or infinite delegation loops.


* **Provenance Anchoring:** Every piece of generated code is tagged with a `[TRUTH_SOURCE]` marker, linking it directly to the documentation chunk in Qdrant that justified the logic.


---


## 4. The Mission Control Dashboard (HUD)


The React-based frontend serves as a real-time **Heads-Up Display (HUD)** for system operations.


* **Real-time Metrics:** WebSockets stream CPU, RAM, and VRAM utilization directly from the Rust sentinel to neon-magenta dials on the UI.


* **The Swarm Monologue:** A live-scrolling terminal feed of internal agent reasoning, allowing the operator to see the "Chain of Thought" before code is executed.


* **Dynamic AST Mapping:** Utilizing ReactFlow to draw the Abstract Syntax Tree (AST) of the project. As the agents build files, the UI visually maps the "Blast Radius" of dependencies.


---


## 5. Forensic Diagnostics


When a task fails in the `Oubliette` sandbox, the system doesn't just crash—it performs a **Forensic Audit**.


* **Sandbox Tracebacks:** Detailed error logs (Syntax, Logic, or Assertion errors) are captured and categorized.


* **HITL Quarantine:** Failed modules are moved to a visual "Quarantine Zone" where a Human-In-The-Loop can inspect the code and the error before deciding to fix, purge, or retry.


* **Audit Trails:** All historical traces are persisted in PostgreSQL, allowing for post-mortem analysis of how the swarm evolved over time.
