SECURITY.MD: PROJECT DAEN (ZERO-TRUST SECURITY MANIFESTO)
1. GLOBAL SECURITY PHILOSOPHY: THE "HOSTILE ENTITY" RULE
In Project DAEN, we treat every AI agent as a hostile entity. Even though they are working for us, LLMs are prone to "prompt injection" (being tricked by external text) or "hallucination" (inventing dangerous commands).

The global rule is: Never Trust, Always Verify. No agent has direct access to the host operating system, the internet, or other agents without going through a security checkpoint.

2. SUB-SECTION SECURITY MEASURES
A. THE RESOURCE GOVERNOR (SYSTEM STABILITY)
OOM PROTECTION: To prevent an agent from crashing the host, the Governor sets a "Hard Ceiling" on RAM usage. If an agent tries to cross it, the Governor terminates the process instantly.

PROCESS ISOLATION: The Governor runs as a compiled binary with minimal permissions. It can see process IDs, but it cannot read the data inside them.

B. THE MESSAGE BUS (COMMUNICATION SECURITY)
JWT VALIDATION: Every request sent between agents must carry a JSON Web Token (JWT). If the Scout tries to talk to the Librarian without a token, the Message Bus ignores the request.

SCHEMA ENFORCEMENT: We use Protobufs to define exactly what a message looks like. If an agent tries to send a "hidden" command inside a text field, the system will reject it because it doesn't fit the "shape" of the allowed data.

ENCRYPTION: All data moving through the bus is encrypted using local keys. Even if someone could "sniff" your local network, the data would be unreadable.

C. THE MEMORY VAULT (DATA INTEGRITY)
WRITE-PROTECTION: The "Truth_DB" (Tier 1) is mounted as Read-Only. No AI can ever modify the official documentation or the "source of truth."

SANITIZATION: Before data is saved into the "Learned_DB," it is scanned for "injection patterns" (text designed to trick the AI later).

ENCRYPTION AT REST: The actual database files on your SSD are encrypted. They only unlock when the DAEN Switchboard is active.

D. THE TESTING SANDBOX (EXECUTION SECURITY)
NETWORK AIR-GAP: The Docker container has its virtual "network cable" unplugged. It can run code, but it cannot send data to the internet or your local Wi-Fi.

NO BIND MOUNTS: The sandbox cannot see your "Documents" or "Downloads" folders. It only sees a tiny, temporary folder with the specific code it needs to test.

TEMPORARY LIFECYCLE: Every sandbox is deleted 100% after the test is finished. No "leftover" files can survive.

3. GLOBAL PROTECTION MEASURES
SECRET SCANNING: The Dev-Daemon automatically runs a tool to look for API keys, passwords, or personal file paths. If it finds one, it refuses to save the file or commit it to Git.

EGRESS PROXY (AEGIS): This is the only "gate" to the outside world. If the Scout needs to download a new manual, Aegis checks the URL against a "Safe List." If the URL isn't on the list, the connection is blocked.

4. FUTURE PLANNING: CLOSED SERVER NETWORKS (MULTI-USER)
While this initial version is for one machine, we are designing it to scale to a closed office or team network in the future.

A. IDENTITY AND ACCESS MANAGEMENT (IAM)
In the future, each person on the network will have a "User Key."

The Librarian will check the Key before answering. (Example: "User A can see Backend Code, but User B is restricted to Frontend only.")

B. FEDERATED AGENTS
We will move from one "Sentinel" to a "Network Sentinel."

If one server in the office is working too hard, the Message Bus will automatically move an AI task to an idle server down the hall to balance the load.

C. AUDIT LOGGING
For a multi-user environment, we will implement an "Immutable Audit Log." Every single command the AI runs will be recorded in a file that cannot be changed or deleted. This allows a Team Lead to see exactly how a piece of code was generated and by whom.

5. REFINEMENT AND DRILLS
As we build, we will perform "Red Team" drills in our dedicated chat threads. We will try to "break" the system by feeding it malicious prompts to see if the Message Bus or the Sandbox catches them. If they don't, we update this SECURITY.MD with a new defense.