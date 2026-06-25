"""
seed.py — populate redis-board with sample data for testing

Usage:
    python seed.py
    python seed.py --url http://localhost:8000
"""

import httpx
import argparse
import asyncio
import random

PLAYERS = [
    ("rony", 9800),
    ("alex", 8750),
    ("priya", 9200),
    ("kai", 7600),
    ("zara", 8100),
    ("marco", 6900),
    ("yui", 9500),
    ("sam", 5400),
    ("lena", 7200),
    ("dev", 8900),
]


async def seed(base_url: str):
    async with httpx.AsyncClient(base_url=base_url) as client:
        # Clear first
        resp = await client.delete("/leaderboard")
        print(f"Reset: {resp.json()['message']}")

        # Post all scores
        for player, score in PLAYERS:
            # Add small random jitter so re-runs vary slightly
            jittered = score + random.randint(-100, 100)
            resp = await client.post("/score", json={"player": player, "score": jittered})
            data = resp.json()
            print(f"  #{data['rank']:>2}  {data['player']:<10} {data['score']:.0f}")

        # Print final board
        print("\n--- Final Leaderboard ---")
        resp = await client.get("/leaderboard?top=10")
        for entry in resp.json()["leaderboard"]:
            print(f"  #{entry['rank']:>2}  {entry['player']:<10} {entry['score']:.0f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    args = parser.parse_args()
    asyncio.run(seed(args.url))
