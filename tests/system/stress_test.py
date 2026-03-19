import asyncio
import httpx
import time
import valkyrie_crypto

# --- CONFIG ---
SECRET = "daen-internal-dev-secret-2026"  # nosec B105
MNEMOSYNE_URL = "http://127.0.0.1:8001/search"
OUBLIETTE_URL = "http://127.0.0.1:8002/run"
CONCURRENT_REQUESTS = 50  # This means 50 Memory + 50 Sandbox = 100 total

async def hit_memory(client, token, i):
    """Simulate an agent furiously searching the database."""
    headers = {"Authorization": f"Bearer {token}"}
    start = time.time()
    try:
        resp = await client.post(MNEMOSYNE_URL, params={"query": "architecture"}, headers=headers)
        return resp.status_code == 200, time.time() - start
    except Exception:
        return False, time.time() - start

async def hit_sandbox(client, token, i):
    """Simulate an agent rapidly testing code."""
    headers = {"Authorization": f"Bearer {token}"}
    code = f"print('Stress test execution {i} - PASS')"
    start = time.time()
    try:
        resp = await client.post(OUBLIETTE_URL, json={"code": code}, headers=headers)
        return resp.status_code == 200, time.time() - start
    except Exception:
        return False, time.time() - start

async def main():
    print(f"[STRESS TEST] Initiating barrage of {CONCURRENT_REQUESTS * 2} concurrent requests...")
    token = valkyrie_crypto.forge_token("stress-tester", "admin", SECRET)

    async with httpx.AsyncClient(timeout=60.0) as client:
        tasks = []
        # Queue up all the requests to fire simultaneously
        for i in range(CONCURRENT_REQUESTS):
            tasks.append(hit_memory(client, token, i))
            tasks.append(hit_sandbox(client, token, i))

        start_time = time.time()
        results = await asyncio.gather(*tasks)  # FIRE!
        total_time = time.time() - start_time

    # Calculate metrics
    successes = sum(1 for r in results if r[0])
    failures = len(results) - successes
    avg_latency = sum(r[1] for r in results) / len(results)

    print("\n[STRESS TEST RESULTS]")
    print(f"Total Time:   {total_time:.2f} seconds")
    print(f"Successes:    {successes}")
    print(f"Failures:     {failures}")
    print(f"Avg Latency:  {avg_latency:.3f} seconds/req")

    if failures == 0:
        print("\n[VERDICT] 🟢 DEAN-OS Infrastructure is ROCK SOLID.")
    else:
        print("\n[VERDICT] 🔴 Bottlenecks detected. We need the Rust Governor.")

if __name__ == "__main__":
    asyncio.run(main())
