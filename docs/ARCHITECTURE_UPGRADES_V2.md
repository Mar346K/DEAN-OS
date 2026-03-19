ARCHITECTURE_UPGRADES_V2.md: The Master Plan (Phases 14 - 16)
1. Executive Summary: The "Glass-Box" Hypervisor
DEAN-OS has successfully achieved local containment, zero-trust security, and basic autonomous orchestration. The objective for Phases 14 through 16 is to shatter the "Cognitive Ceiling" of local 8B models, transform the system from a "black box" into a highly observable distributed network, and introduce operational reliability through Human-In-The-Loop (HITL) fail-safes and FinOps guardrails.

2. Phase 14: Compiler-Aware Context & Cognitive Scaling
The Goal (Why): Local 8B models hallucinate imports and rewrite entire files when they lack deep architectural context. Furthermore, routing every request through a heavy model wastes compute and latency. We must give the agents a compiler-level understanding of the codebase and scale compute dynamically.

The Implementation (How):

The Symbolic Dependency Mapper (AST): DEAN-OS stops treating files as raw text strings. Using Python’s ast (Abstract Syntax Tree) module, the system parses the /workspace and builds a read-only "Global Export Map" (a dictionary of all existing classes, functions, and their required arguments). This map is injected into the Coder’s prompt, mathematically preventing hallucinated imports.

The Smart-Tier Router: A complexity classifier sitting inside Sycophant.

Tier 1 (Local 8B): Handles syntax generation, boilerplate, and initial unit tests.

Tier 2 (High-End API 70B+): Automatically triggered only if the Assembly Line hits a Level-2 failure (e.g., the local 8B model fails to fix a bug after two recursive attempts in the Sandbox).

Plan to Prove (Verification):

[ ] Test 14.1 (AST Awareness): Create a highly obscure custom function in file_a.py. Task the Architect/Coder to write file_b.py that utilizes it. Verify the LLM correctly imports and uses the exact function signature without guessing, strictly referencing the AST map.

[ ] Test 14.2 (Cognitive Scaling): Force a complex logic failure in Oubliette. Verify Sycophant uses the 8B model for Attempt 1 and 2, detects the recursive failure, dynamically routes the traceback to the 70B model for Attempt 3, and successfully patches the logic.

3. Phase 15: Deep Observability & Distributed Tracing
The Goal (Why): Multi-agent systems are notoriously difficult to debug because they act as black boxes. To prove enterprise readiness, DEAN-OS must emit real-time telemetry so a human operator can watch the "heartbeat" and thought process of the swarm.

The Implementation (How):

OpenTelemetry Integration: Valkyrie stamps every JWT and inter-process API call with a W3C-compliant trace_id.

The Provenance Dashboard: Aethelgard (the Rust server) aggregates these traces alongside its hardware metrics (RAM, GPU thermals) and exposes them to a Prometheus/Grafana dashboard (or a custom lightweight UI).

Value: A human operator can visually watch a request enter the Architect, spawn a child-trace to Mnemosyne (showing exactly which vector chunk was retrieved), hand off to the Coder, and execute in Oubliette, all overlaid on top of host CPU spikes.

Plan to Prove (Verification):

[ ] Test 15.1 (Distributed Trace): Submit a prompt. Open the observability dashboard. Verify you can see a unified Waterfall Trace charting the lifespan of the request across all 5 agents, with accurate millisecond latency for each microservice hop.

[ ] Test 15.2 (Provenance Anchor): In the trace output, verify the Coder's span explicitly lists the [TRUTH_SOURCE] document ID it used to generate the logic.

4. Phase 16: Operational Reliability (HITL & FinOps)
The Goal (Why): Infinite loops and unmonitored API calls burn money. A production-grade system knows when to stop trying and ask for human help, and it enforces hard financial boundaries on API spending.

The Implementation (How):

The "Checkpoint" Interceptor (HITL): If Sycophant hits Attempt 3 of a Self-Healing loop, it does not quarantine the file. It halts the Assembly Line, saves the exact state, and alerts the user: "Sandbox execution failed 3 times. Awaiting human guidance." It presents the traceback and the code. The human types a one-sentence fix (e.g., "You forgot to initialize the database connection"), and the swarm resumes.

FinOps Guardrails (Valkyrie): Valkyrie tracks the token count and API cost of the Tier 2 (70B) model. A budget.yaml defines a strict limit (e.g., $0.10 per task). If an agent requests a token that would push the task over budget, Valkyrie violently drops the JWT and terminates the swarm.

Plan to Prove (Verification):

[ ] Test 16.1 (Interactive Debugging): Sabotage a piece of generated code with a subtle logical flaw. Let Oubliette fail it twice. On Attempt 3, verify the system halts and prompts the terminal. Provide a human text hint, and verify the Coder successfully integrates your hint to pass the test.

[ ] Test 16.2 (FinOps Circuit Breaker): Set the task budget to $0.01. Force the system into a complex Tier-2 routing loop. Verify Valkyrie intercepts the 3rd request, logs BUDGET_EXCEEDED, and gracefully spins down the Docker containers to save money.

The Execution Strategy
This blueprint gives you a flawless narrative for interviews. You are demonstrating Static Code Analysis (Phase 14), Cloud-Native Observability (Phase 15), and Engineering Economics (Phase 16).

The highest-leverage item on this list—and the one that will instantly fix the 8B model's hallucination problem—is the Symbolic Dependency Mapper.
