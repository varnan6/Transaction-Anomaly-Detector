import asyncio
import json
import os
from typing import List
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        if not self.active_connections:
            return
        message = json.dumps(data)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(push_updates_to_clients())
    yield
    task.cancel()


app = FastAPI(title="Fraud Detection API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_redis():
    return await aioredis.from_url(
        f"redis://{REDIS_HOST}:{REDIS_PORT}",
        decode_responses=True
    )


@app.get("/api/health")
async def health():
    try:
        r = await get_redis()
        await r.ping()
        await r.aclose()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/api/stats")
async def get_stats():
    r = await get_redis()

    total_tx = await r.get("stats:total_transactions") or "0"
    fraud_count = await r.get("stats:fraud_detected") or "0"
    total_volume = await r.get("stats:total_volume") or "0"
    last_batch_size = await r.get("stats:last_batch_size") or "0"
    last_batch_time = await r.get("stats:last_batch_time") or "never"

    categories = [
        "grocery", "restaurant", "gas_station", "online_retail",
        "travel", "entertainment", "pharmacy", "electronics",
        "clothing", "atm_withdrawal"
    ]

    category_counts = {}
    for cat in categories:
        count = await r.get(f"stats:category:{cat}") or "0"
        category_counts[cat] = int(count)

    total_tx_int = int(total_tx)
    fraud_int = int(fraud_count)

    await r.aclose()

    return {
        "total_transactions": total_tx_int,
        "fraud_detected": fraud_int,
        "fraud_rate": round(fraud_int / max(total_tx_int, 1) * 100, 2),
        "total_volume_usd": round(float(total_volume), 2),
        "last_batch_size": int(last_batch_size),
        "last_batch_time": last_batch_time,
        "category_breakdown": category_counts,
    }


@app.get("/api/alerts")
async def get_alerts(limit: int = 50):
    r = await get_redis()
    raw_alerts = await r.lrange("alerts:recent", 0, limit - 1)
    alerts = []
    for raw in raw_alerts:
        try:
            alerts.append(json.loads(raw))
        except json.JSONDecodeError:
            pass
    await r.aclose()
    return {"alerts": alerts, "count": len(alerts)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def push_updates_to_clients():
    r = await get_redis()

    while True:
        try:
            if manager.active_connections:
                total_tx = int(await r.get("stats:total_transactions") or 0)
                fraud_count = int(await r.get("stats:fraud_detected") or 0)
                total_volume = float(await r.get("stats:total_volume") or 0)

                newest_alerts = await r.lrange("alerts:recent", 0, 4)
                parsed_alerts = []
                for raw in newest_alerts:
                    try:
                        parsed_alerts.append(json.loads(raw))
                    except Exception:
                        pass

                await manager.broadcast({
                    "type": "update",
                    "stats": {
                        "total_transactions": total_tx,
                        "fraud_detected": fraud_count,
                        "fraud_rate": round(fraud_count / max(total_tx, 1) * 100, 2),
                        "total_volume_usd": round(total_volume, 2),
                    },
                    "latest_alerts": parsed_alerts,
                    "timestamp": asyncio.get_event_loop().time(),
                })
        except Exception as e:
            print(f"Broadcaster error: {e}")

        await asyncio.sleep(1)
