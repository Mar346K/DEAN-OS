# DEAN-OS Architectural Upgrade: Project Yggdrasil
**Status:** Planning / Research
**Start Date:** 2026-03-31
**Goal:** Transition from a monolithic, single-task tool to a multi-tenant, self-healing Agentic OS.

## 1. Core Vision
To build an enterprise-grade agentic infrastructure that utilizes high-density model specialization, deterministic security guardrails, and autonomous chaos engineering (Ragnarök) to produce production-ready software on consumer-grade hardware.

## 2. Git Strategy & Isolation
- **Branch:** `feature/yggdrasil-re-architecture`
- **Main Branch Status:** Locked (Stable Phase 26).
- **Merge Criteria:** Must pass the new Ragnarök Hardware Stress Test and the Valkyrie 2.0 Symbolic Gate.

## 3. The Five Pillars of Yggdrasil

### Pillar 1: Multi-Tenant Foundation (Priority 1)
* **The Change:** Move from `/staging/workspace` to `/staging/projects/{project_id}`.
* **Implementation:** * Add a `Project` model to Postgres.
    * Refactor `Mnemosyne` to use Qdrant payload filters for `{project_id}`.
    * Refactor `Oubliette` to mount project-specific Docker volumes.
* **Why:** Prevents "Context Bleed" where code logic from unrelated projects contaminates the LLM's reasoning.

### Pillar 2: Rust-Unified Performance (VDB-GC)
* **The Change:** Implement the Vector Database Garbage Collector in **Rust** (not Go).
* **Implementation:**
    * Bake VDB-GC into the `aethelgard` or `valkyrie-crypto` crates.
    * Use `xxhash` for content-addressable fingerprinting.
    * Implement **Temporal Weighting**: Keep the "Head" (latest versions), prune the "Scar Tissue" (redundant intermediate steps).
* **Why:** Eliminates the "Polyglot Tax" and leverages Rust’s memory safety for high-speed vector deduplication.

### Pillar 3: Deterministic Security (Valkyrie 2.0)
* **The Change:** Switch from "Neural Security" to "Symbolic Security."
* **Implementation:** * Use the Python `ast` module or `tree-sitter` to generate a deterministic Logic Map.
    * Pass the Map to the Rust Core for verification against `policy.yaml`.
    * Use **MiMo-V2-Flash** only for high-speed intent interpretation, not permission granting.
* **Why:** Prevents "Neural Lying" where an LLM hallucinates a safe-looking JSON response to hide malicious code.

### Pillar 4: Model Tiering & VRAM Management
* **The Change:** Tier models to balance reasoning depth with UI responsiveness.
* **Strategy:**
    * **Hot Resident:** `Qwen-2.5-Coder-14B` (stays in VRAM for coding/fixing).
    * **On-Demand:** `Qwen-2.5-Coder-32B` (summoned only for initial architecture or complex refactors).
    * **Utility MoE:** `MiMo-V2-Flash` (used for rapid-fire security/chaos checks).
* **Mitigation:** Hardware Watchdog in Rust to ensure 100% VRAM release during swaps.

### Pillar 5: The Ragnarök Protocol (Chaos Engineering)
* **The Change:** Autonomous adversarial red-teaming.
* **Implementation:**
    * Adversarial Middleware in `gateway.py`.
    * Intentionally inject Logic Poisoning and Hardware Exhaustion scenarios.
    * **Immunity Loop:** Successful "Heals" are logged in Mnemosyne as persistent constraints.
* **Why:** Builds a "Systemic Immune System" that learns from its own failures before they hit production.

## 4. Hardware Constraints (Intel Arc 16GB)
- **Max Model Size:** 32B (IQ3_M quantization).
- **Context Limit:** 4096 tokens (Enforced by UI Saturation Dial).
- **KV Cache:** `q4_0` compression (TurboQuant logic).

## 5. Definition of Done
1.  System handles two unrelated projects simultaneously without drift.
2.  Rust VDB-GC keeps Qdrant memory usage under 2.5GB.
3.  Valkyrie 2.0 blocks a "Ragnarök-injected" prompt without LLM assistance.
