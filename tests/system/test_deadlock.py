import httpx
import asyncio

AETHELGARD_URL = "http://127.0.0.1:8003/trace"
TRACE_ID = "task-blackjack-001"

async def simulate_infinite_loop():
    print("--- INITIATING DAG DEADLOCK PENETRATION TEST ---")

    # We simulate a "Coder" constantly failing QA and bouncing back to the "Analyzer"
    delegation_chain = [
        ("Architect", "Coder"),
        ("Coder", "Analyzer"),
        ("Analyzer", "Coder"),
        ("Coder", "Analyzer"),
        ("Analyzer", "Coder"),
        ("Coder", "Analyzer"), # <-- Aethelgard should kill it here!
        ("Analyzer", "Coder")
    ]

    async with httpx.AsyncClient() as client:
        for i, (source, target) in enumerate(delegation_chain):
            print(f"\n[SWARM] Agent '{source}' delegating to '{target}'...")

            payload = {
                "trace_id": TRACE_ID,
                "source_agent": source,
                "target_agent": target
            }

            resp = await client.post(AETHELGARD_URL, json=payload)
            result = resp.json()

            if result.get("status") == "DEADLOCK_PREVENTED":
                print(f"🛑 [SUCCESS] Aethelgard intervened on request {i+1}: {result.get('message')}")
                return
            else:
                print(f"✅ [OK] Aethelgard approved hop.")

if __name__ == "__main__":
    asyncio.run(simulate_infinite_loop())
