The Institutional Intelligence Layer (Phases 17 - 19)
1. Executive Summary: The Predictive Systems Architect
DEAN-OS has successfully achieved local containment, zero-trust security, distributed tracing, and hard financial guardrails (Phases 1 - 16). The objective for Phases 17 through 19 is to transition DEAN-OS from a reactive code-generator into a Predictive Systems Architect.

By building Institutional Memory, Data Loss Prevention (DLP), and a real-time visual frontend, the swarm will be able to analyze legacy codebases, understand the "why" behind historical bugs, securely leverage cloud intelligence for complex logic, and visually demonstrate the "Blast Radius" of proposed changes before executing them.

2. Phase 17: The Forensic Harvester & Institutional Memory
The Goal (Why): Reading a codebase's current state is not enough. To safely modify legacy systems, the swarm must understand historical volatility (which files break the most) and functional dependencies (which functions call each other). We need to build a Project Intelligence Manifest (PIM) that acts as the swarm's Institutional Memory.

The Implementation (How):

Git Scar Tissue (Churn Analysis): Upgrade the ast_mapper.py to integrate with GitPython. The mapper will scan the .git directory to calculate a "Churn Score" for every file and function, identifying high-risk bug zones.

Call-Graph Mapping: Expand the Python AST parser to map the Directed Acyclic Graph (DAG) of internal function calls, allowing the swarm to calculate the downstream impact of altering a specific module.

Plan to Prove (Verification):

[ ] Test 17.1 (Scar Tissue Detection): Run the Forensic Harvester on the DEAN-OS repo. Verify the resulting PIM correctly identifies manager.py or gateway.py as high-churn "hotspots" based on commit history.

[ ] Test 17.2 (Call-Graph Extraction): Verify the PIM correctly maps that manager.py depends on coder.py, which depends on ast_mapper.py.

3. Phase 18: The Hybrid Air-Lock (DLP Egress Guard)
The Goal (Why): Local 8B/14B models handle 90% of tasks, but enterprise-grade architecture occasionally requires the reasoning power of a 70B+ cloud model (Claude 3.5, Gemini 1.5 Pro). To maintain Zero-Trust, DEAN-OS must mathematically guarantee that proprietary secrets or PII never leave the local machine.

The Implementation (How):

Valkyrie DLP Firewall: Upgrade the Rust valkyrie-crypto library to include an Egress Guard. Before gateway.py sends a Tier-3 prompt to an external API, the payload is piped through Rust.

Regex & Entropy Scrubbing: Valkyrie scans the payload for high-entropy strings (API keys, JWTs) and hardcoded proprietary variable names (e.g., INTERNAL_DB_PASSWORD), redacting them with [REDACTED_BY_VALKYRIE] before transmission.

Plan to Prove (Verification):

[ ] Test 18.1 (The Air-Lock Intercept): Hardcode a fake AWS access key into a prompt. Force gateway.py to route to a mocked external API. Verify Valkyrie successfully intercepts, scrubs the key, and logs a DLP warning.

4. Phase 19: Mission Control & Visual Observability
The Goal (Why): A multi-agent system operating entirely in the terminal is difficult to monitor at scale. DEAN-OS requires a visual command center to prove its operational safety, allowing human operators to watch the swarm's heartbeat, trace execution, and simulate changes.

The Implementation (How):

Stitch 2.0 Frontend: Utilize Google Stitch 2.0 to generate a reactive, force-directed "Vibe Design" dashboard (React/Tailwind).

Live Rust Telemetry (WebSockets): Upgrade Aethelgard's /metrics endpoint from REST to Server-Sent Events (SSE) or WebSockets, broadcasting RAM, VRAM, and active deadlocks to the UI in real-time.

The Blast Radius Simulator: A visual representation of the PIM. When the user selects a file in the UI, the dependency web highlights all downstream files in red, showing exactly what might break if the file is altered.

Plan to Prove (Verification):

[ ] Test 19.1 (Live Telemetry Stream): Boot the React frontend. Run a heavy inference task in Ollama. Verify the VRAM usage spikes in real-time on the UI without refreshing the page.

[ ] Test 19.2 (Blast Radius UI): Click on valkyrie-crypto in the UI graph. Verify that oubliette and sycophant instantly glow red, demonstrating the visual dependency link.
