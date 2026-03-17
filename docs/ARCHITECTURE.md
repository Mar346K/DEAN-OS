ARCHITECTURE.MD: PROJECT DAEN (DISTRIBUTED AUTONOMOUS ENGINEERING NETWORK)
1. VISION AND PURPOSE
Project DAEN is a local-first system designed to automate backend software engineering. The goal is to create a "digital colleague" that can research libraries, write code, and verify it—all on your own hardware without needing the cloud.

By building this, we solve three main problems:

DATA PRIVACY: Your intellectual property and code never leave your machine.

COST: You use your own GPU/CPU instead of paying for expensive API subscriptions.

ACCURACY: Most AI "hallucinates" old or fake code. DAEN uses a real-time research-and-test loop to ensure code actually works before you see it.

2. THE CORE SYSTEM DESIGN (WHY AND HOW)
The system is split into specialized "services" that talk to each other over a local network. This is called a Microservice Architecture. We do this so that if one part crashes (like an AI agent getting confused), it doesn't break the whole computer.

A. THE RESOURCE GOVERNOR (THE BRAIN STEM)
WHY: Running large AI models can eat up all your RAM and crash your computer.

HOW: Written in Rust (for speed and safety), this stays awake and watches your CPU/RAM/VRAM. If the computer is running out of memory, it kills the lowest-priority AI task to save the host. It also checks your hardware at startup to see what size AI models your machine can handle.

B. THE MESSAGE BUS (THE NERVOUS SYSTEM)
WHY: Agents need to send large amounts of data to each other without waiting in a "line."

HOW: We use Redis and Protobufs. Redis acts as the "mailroom." Every message is strictly formatted (Protobufs) and signed with a digital key (JWT). If a message looks weird or malicious, the bus drops it immediately.

C. THE MEMORY VAULT (THE LIBRARY)
WHY: AI needs to remember what it learned and where it got the info.

HOW: This is a 5-tier database system. Every piece of info has a "Traceability Marker":

[TRUTH_SOURCE]: Verified manuals and official docs.

[DREAM_HYPOTHESIS]: Experimental ideas the AI came up with.

[LEARNED_HISTORY]: Ideas that were tested in the sandbox and actually worked.

[SUMMARY_STATE]: A "shorthand" note of what the AI is currently doing.

[VERSION_RAW]: The actual code files on your drive.

D. THE AGENT TEAM (THE WORKERS)
WHY: One AI can't do everything. We need specialists.

HOW:

THE SCOUT: Finds and downloads the latest library documentation.

THE LIBRARIAN: Reads the docs and plans the software architecture.

THE DEV-DAEMON: Handles the actual file writing and Git commits.

E. THE TESTING SANDBOX (THE PROVING GROUND)
WHY: You should never run AI-generated code directly on your main machine.

HOW: A "Docker" container with no internet access. The AI writes code, sends it to the sandbox, and the sandbox tries to run it. It sends back a "PASS" or "FAIL" report. If it fails, the AI has to try again.

3. SECURITY AND PROTECTION
Each area has its own "shield":

NETWORK: Aegis (the proxy) monitors all internal traffic. No AI agent can talk to the internet unless specifically authorized.

HARDWARE: Memory is "sliced." An agent can only see the RAM it was given, protecting the rest of your system data.

DATA: Sensitive info is encrypted. The Dev-Daemon scans code for passwords or private paths before anything is saved.

4. THE STARTUP AND SHUTDOWN (THE SWITCHBOARD)
We use a single command-line tool to manage the whole system:

STARTUP: Validates hardware -> Boots Governor -> Boots Message Bus -> Starts Agents.

SHUTDOWN: Saves all current work -> Flushes the Sandbox -> Gracefully closes all processes.

5. PLANNED PHASES OF DEVELOPMENT
INFRASTRUCTURE: Build the "Factory" (the CI/CD pipeline) to test our own code.

STABILITY: Build the Rust-based Resource Governor to protect the machine.

KNOWLEDGE: Set up the Memory Vault and start downloading "Truth" documentation.

COMMUNICATION: Connect everything with the Message Bus and security keys.

AUTONOMY: Turn on the Agents and the Sandbox to start the "Dream and Test" loops.

6. ROOM FOR IMPROVEMENT
This is a living document. As we build each part in its own dedicated thread, we will likely find better ways to handle things like "Context Flushing" (how the AI refreshes its memory) or "Cross-Platform Support" (making sure this works on both Windows and Mac). We will update this master file as those discoveries are made.