Here is the expanded, CTO-ready version of your `ARCHITECTURE_UPGRADES.md`.

I have restructured the roadmap to absorb the four massive backend upgrades. I expanded the timeline to **Phase 13** to ensure we don't crowd the development cycles. Most importantly, every single phase now includes the **"Why,"** the **"How,"** and a strict **"Plan to Prove" (Verification Matrix)** so you can mathematically guarantee each phase is complete before moving on.

***

# ARCHITECTURE_UPGRADES.md: The Master Plan (Phases 9 - 13)

## 1. Executive Summary: The "Zero-Fail" Agentic OS
DEAN-OS is transitioning from a secure functional prototype into a **Deterministic, ACID-compliant Agentic Hypervisor**. The goal is to move past standard AI code generation into a system that enforces rigid grammar at the inference level, mathematically prevents infinite delegation loops, optimizes compute economics, and treats agentic workflows as atomic database transactions.

---

## 2. Phase 9: The Assembly Line & Workspace Integration
**The Goal (Why):** Generalist AI agents suffer from severe context drift. We must give the AI "hands" and eliminate hallucination through role specialization.

**The Implementation (How):**
The 5-Agent Production Suite:
1. **The Architect:** Receives user intent; drafts a multi-file JSON blueprint including function signatures.
2. **The Main Coder:** Consumes the blueprint; implements logic for one file at a time.
3. **The Tester:** Generates adversarial `pytest` suites and boundary checks.
4. **The Analyzer:** Executes code in the `Oubliette` sandbox; parses tracebacks to differentiate between "Loud Failures" (syntax) and "Silent Failures" (logic).
5. **The Deployment Agent:** The only agent with write-access to the host `/workspace`. Moves validated modules out of staging.

**Plan to Prove (Verification):**
* [ ] **Test 9.1:** Deploy a "Hello World" API task. Verify the Architect passes a JSON payload to the Coder, the Coder writes the script, the Tester writes a passing `pytest`, and the Deployment Agent successfully moves it to `/workspace`.
* [ ] **Test 9.2:** Check volume shadowing to ensure `Oubliette` can read the staging folder but cannot access the root host system.

---

## 3. Phase 10: The Governance & Observability Shield
**The Goal (Why):** Solve "Identity Dark Matter." Enterprise systems require immutable proof of *why* an AI made a decision, and strict boundaries on *what* it is allowed to do.

**The Implementation (How):**
* **The Provenance Graph (Auditability):** A dashboard tracing the AI's "Train of Thought." Every action logs a node linking back to the specific `[TRUTH_SOURCE]` document in `Mnemosyne` that justified the code.
* **Agentic Policy Decision Point (PDP):** A YAML-based `policy.yaml` enforcing Least-Privilege Access Control. Example: `Agent: Scout | Perms: [Network_Egress, Read_Only]`. `Valkyrie` (Rust) reads this YAML and rejects JWTs attempting actions outside their scope.

**Plan to Prove (Verification):**
* [ ] **Test 10.1 (Provenance):** Query the system to write a proxy server. Verify the audit log points directly to the `httpx` documentation chunk in Qdrant.
* [ ] **Test 10.2 (PDP Firewall):** Forge a valid JWT for the "Scout" agent, but attempt to send a payload to the "Deployment" write-file endpoint. Verify `Valkyrie` violently drops the request with an HTTP 403 Forbidden.

---

## 4. Phase 11: The Resilience Suite & ACID Rollbacks
**The Goal (Why):** Multi-agent swarms are historically destructive and can ruin local workspaces. Furthermore, we must mathematically verify system safety against resource exhaustion.

**The Implementation (How):**
* **Atomic "Time-Travel" Rollbacks (ACID Compliance):** Agent workflows are treated as atomic database transactions. Before a task starts, the Deployment Agent triggers a lightweight snapshot of `/workspace` and `Mnemosyne`. If the Analyzer detects a failure after 3 retries, the system deletes corrupted vectors and reverts files to the exact millisecond before the task began.
* **The Chaos Monkey (`ragnarok.py`):** An adversarial script designed to attack DEAN-OS. It will attempt to spoof identities, exhaust memory, and poison search vectors.

**Plan to Prove (Verification):**
* [ ] **Test 11.1 (Rollback):** Populate `/workspace` with a clean script. Task the swarm to modify it. Deliberately sabotage the `Tester` agent so it fails. Verify the system automatically restores the clean script and purges any bad context from `Mnemosyne`.
* [ ] **Test 11.2 (Chaos):** Run `ragnarok.py` to spike sandbox memory to 2GB. Verify the Rust `Aethelgard` Sentinel catches the pressure and executes a `SIGKILL` before host RAM exceeds 90%.

---

## 5. Phase 12: Inference Determinism & Compute Economics
**The Goal (Why):** Parsing JSON via Regex is fragile and breaks pipelines. Furthermore, routing simple syntax fixes through a massive 70B parameter model wastes electricity, latency, and VRAM.

**The Implementation (How):**
* **Token-Level Determinism (Grammar FSM):** DEAN-OS bypasses string parsing. It uses strict Grammar Finite State Machines (via tools like `outlines` or `llama.cpp` grammar rules) to physically mask logits at the inference level. Syntax errors in JSON/AST outputs become mathematically impossible.
* **Compute-Aware Semantic Routing:** A caching layer in front of `Sycophant`. If a user intent embeds to a 98% similarity with a cached task, bypass inference completely. If it is a simple fix, route to a 1.5B fast model. Only wake up the heavy 70B/32B model for deep architectural reasoning.

**Plan to Prove (Verification):**
* [ ] **Test 12.1 (Determinism):** Give the LLM a highly confusing, adversarial prompt but enforce a strict JSON schema via the FSM. Verify the output parses via `json.loads()` with 100% success over 50 iterations.
* [ ] **Test 12.2 (Economics):** Request a boilerplate FastAPI script. Measure latency. Request the exact same script again. Verify the Semantic Router catches the similarity, bypasses the LLM, and returns the cached script in under 50ms.

---

## 6. Phase 13: Graph-Theory Deadlock Detection
**The Goal (Why):** The most expensive failure mode of agentic swarms is the infinite delegation loop (Agent A asks B, B asks A, burning compute forever).

**The Implementation (How):**
* **DAG-Based Deadlock Breaker:** Real-time Graph Theory monitoring in Rust. `Valkyrie` stamps every inter-agent request with a Trace ID. `Aethelgard` maintains an in-memory Directed Acyclic Graph (DAG) of the conversation. If it detects a cycle (`Architect -> Coder -> Analyzer -> Architect`) happening more than twice with identical semantic payloads, it breaks the circuit and halts the swarm.

**Plan to Prove (Verification):**
* [ ] **Test 13.1 (Deadlock Prevented):** Write a hardcoded mock script where the `Coder` agent explicitly delegates back to the `Architect` in an infinite loop. Run the script. Verify `Aethelgard` detects the cycle on the 3rd iteration, terminates the processes, and logs `DEADLOCK_PREVENTED`.

---

## 7. Current "Zombie" Audit & Cleanup Status
- [x] Redundant Files: Deleted `infrastructure/containers/agent.Dockerfile`.
- [x] Typos Fixed: `valkyrie-crytpo` renamed to `valkyrie-crypto`.
- [x] Folder Flattening: Services moved out of `/src` for cleaner imports.
- [x] Git Sanitization: `.lock` and `storage/` files removed from the index.
- [x] Infrastructure Unified: `daenctl.py` now boots Python and Rust services simultaneously.
