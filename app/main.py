from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as aioredis
import os

app = FastAPI(title="redis-board", description="Live leaderboard powered by Redis ZSet")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
LEADERBOARD_KEY = "leaderboard:global"

redis_client: aioredis.Redis = None


@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)


@app.on_event("shutdown")
async def shutdown():
    await redis_client.aclose()


# --- Models ---

class ScorePayload(BaseModel):
    player: str
    score: float


# --- Routes ---

@app.post("/score", summary="Add or update a player's score")
async def post_score(payload: ScorePayload):
    """
    Uses ZADD — if the player already exists, their score is updated.
    ZSet automatically keeps members sorted by score.
    """
    await redis_client.zadd(LEADERBOARD_KEY, {payload.player: payload.score})
    rank = await redis_client.zrevrank(LEADERBOARD_KEY, payload.player)
    return {
        "player": payload.player,
        "score": payload.score,
        "rank": rank + 1,  # 0-indexed → 1-indexed
    }


@app.get("/leaderboard", summary="Get top N players")
async def get_leaderboard(top: int = 10):
    """
    ZREVRANGE with WITHSCORES — returns highest scores first.
    Redis returns a flat list: [member, score, member, score, ...]
    We zip it into clean dicts.
    """
    if top < 1 or top > 100:
        raise HTTPException(status_code=400, detail="top must be between 1 and 100")

    # zrevrange returns list of (member, score) tuples when withscores=True
    results = await redis_client.zrevrange(LEADERBOARD_KEY, 0, top - 1, withscores=True)

    return {
        "leaderboard": [
            {"rank": i + 1, "player": member, "score": score}
            for i, (member, score) in enumerate(results)
        ],
        "total_players": await redis_client.zcard(LEADERBOARD_KEY),
    }


@app.get("/player/{name}", summary="Get a single player's rank and score")
async def get_player(name: str):
    score = await redis_client.zscore(LEADERBOARD_KEY, name)
    if score is None:
        raise HTTPException(status_code=404, detail=f"Player '{name}' not found")

    rank = await redis_client.zrevrank(LEADERBOARD_KEY, name)
    return {"player": name, "score": score, "rank": rank + 1}


@app.delete("/player/{name}", summary="Remove a player from the leaderboard")
async def delete_player(name: str):
    removed = await redis_client.zrem(LEADERBOARD_KEY, name)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Player '{name}' not found")
    return {"message": f"Player '{name}' removed"}


@app.delete("/leaderboard", summary="Wipe the entire leaderboard")
async def reset_leaderboard():
    await redis_client.delete(LEADERBOARD_KEY)
    return {"message": "Leaderboard cleared"}


@app.get("/health")
async def health():
    await redis_client.ping()
    return {"status": "ok", "redis": "connected"}
