# redis-board

A live leaderboard API built with **FastAPI + Redis ZSet**.

Demonstrates the core Redis pattern: use the right data structure for the problem.
A sorted set (`ZSet`) is the perfect fit for leaderboards — insertion, update, and rank lookup are all O(log N).

---

## Redis commands used

| Endpoint | Redis command | What it does |
|---|---|---|
| `POST /score` | `ZADD key score member` | Adds or updates a member's score |
| `POST /score` (rank) | `ZREVRANK key member` | Returns rank (0-indexed, high→low) |
| `GET /leaderboard` | `ZREVRANGE key 0 N WITHSCORES` | Top N members, sorted high→low |
| `GET /leaderboard` (count) | `ZCARD key` | Total number of members |
| `GET /player/:name` | `ZSCORE key member` | A single member's score |
| `DELETE /player/:name` | `ZREM key member` | Remove a member |
| `DELETE /leaderboard` | `DEL key` | Wipe the whole key |

---

## Quickstart

```bash
# 1. Start everything
docker compose up --build

# 2. Seed with sample players (new terminal)
pip install httpx
python seed.py

# 3. Hit the API
curl http://localhost:8000/leaderboard?top=5

# 4. Interactive docs
open http://localhost:8000/docs
```

---

## Example requests

```bash
# Add / update a score
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"player": "rony", "score": 9999}'

# Get top 3
curl http://localhost:8000/leaderboard?top=3

# Check a specific player
curl http://localhost:8000/player/rony

# Remove a player
curl -X DELETE http://localhost:8000/player/rony
```

---

## Key concept: why ZSet?

A Redis Sorted Set stores `(member, score)` pairs and keeps them **automatically sorted by score**.
Unlike a regular set, each member has a floating-point score attached.

```
ZADD leaderboard:global 9800 "rony"
ZADD leaderboard:global 8750 "alex"
ZREVRANGE leaderboard:global 0 2 WITHSCORES
# → ["rony", "9800", "alex", "8750"]
```

Operations are O(log N) — fast even with millions of players.
All writes are atomic — no race conditions on concurrent score updates.

---

## Project structure

```
redis-board/
├── app/
│   └── main.py          # FastAPI app
├── docker-compose.yml   # FastAPI + Redis services
├── Dockerfile
├── requirements.txt
├── seed.py              # Populate test data
└── README.md
```

---

## Extending this

- Add a `TTL` on player keys to auto-expire inactive players
- Use `ZINCRBY` instead of `ZADD` for incremental scoring (e.g. +10 per kill)
- Add a `GET /leaderboard/around/{player}` endpoint using `ZREVRANK` + `ZREVRANGE`
- Plug the leaderboard key into throttle-gate's Redis instance — two features, one Redis
