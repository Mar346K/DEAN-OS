# SECURITY_MANIFESTO.md: The Zero-Trust AI Framework

## 1. Global Security Philosophy: "The Hostile Entity"

In DEAN-OS, we treat every AI agent as a **Hostile Entity**. LLMs are susceptible to prompt injection and hallucination. Therefore, no agent is ever granted direct access to the host OS, the internet, or other agents without passing through a verified security checkpoint.


---


## 2. The Valkyrie Vault: Zero-Knowledge Encryption

API keys (OpenAI, Anthropic, Gemini) are never stored in plaintext on disk or in environment variables.

* **Encryption Standard:** AES-256-GCM (Authenticated Encryption with Associated Data).
* **Implementation (Rust):** Utilizing the `aes-gcm` and `sha2` crates.
* **Key Derivation:** A perfect 32-byte master key is derived via SHA-256 from the `DAEN_INTERNAL_SECRET`.
* **Sealing Logic:** When a key is input via the UI, it is immediately "sealed" into a hex-encoded binary blob with a unique 96-bit nonce. Plaintext is purged from memory instantly.


---


## 3. The Egress Guard: Data Loss Prevention (DLP)

To leverage Cloud AI (Tier-2 reasoning) without sacrificing data sovereignty, DEAN-OS utilizes a **Regex-based Egress Scrubber** written in Rust.

* **Payload Redaction:** Before any prompt is routed to a Cloud API, it is piped through Valkyrie.
* **Redaction Targets:**
  * High-entropy strings (API Keys, JWTs).
  * Proprietary variable names and internal IP addresses.
  * User-defined sensitive terms (e.g., `INTERNAL_DB_PASSWORD`).
* **Result:** The Cloud LLM receives a "sanitized" prompt, ensuring proprietary logic or secrets never leave the local air-gap.


---


## 4. Identity & Access Management (IAM)

Inter-service communication is secured via **JSON Web Tokens (JWT)**.

* **Role-Based Access Control (RBAC):** Every agent (Architect, Coder, etc.) is issued a JWT with specific "Scopes."
* **Validation:** The `Valkyrie` module validates every token against a `policy.yaml`.
* **Example:** If the "Scout" agent attempts to call a `write_file` endpoint, the JWT is rejected because the agent lacks the required write-scope.


---


## 5. Execution Isolation: The Oubliette Sandbox

AI-generated code is inherently untrusted.

* **Containerization:** All code execution occurs inside the `Oubliette` Docker container.
* **Network Air-Gap:** The sandbox container has no virtual "network cable." It cannot reach the internet or the local Wi-Fi.
* **Zero Persistence:** Sandboxes are ephemeral. Every execution starts with a clean-slate filesystem that is 100% purged after the test cycle.


---


## 6. Financial Security (FinOps)

Security also means protecting the user's wallet from "Infinite Loop" bugs.

* **The Circuit Breaker:** Valkyrie tracks the estimated token cost of every Tier-2 request.
* **Hard Limits:** If a task attempts to exceed the user-defined budget (e.g., $0.01), Valkyrie violently revokes the agent's execution rights and halts the swarm.
