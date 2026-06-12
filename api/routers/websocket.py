import json
import logging
import os

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
log = logging.getLogger(__name__)


@router.websocket("/ws/flags")
async def websocket_flags(websocket: WebSocket):
    """
    the frontend connects here and stays connected, whenever the worker
    catches a high risk flag to redis, we pick it up and forward it to the frontend
    
    on connect, we'd replay the last 20 flags so the client doesnt start w an empty feed
    """
    await websocket.accept()
    log.info("websocket client connected")
    
    r = aioredis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True,
    )
    
    try:
        # replay recent flags so the feed isnt empty on connect
        recent = await r.lrange("recent_high_risk_flags", 0, 19)
        for raw in reversed(recent):
            await websocket.send_text(raw)
            
        # subscribe to the pub/sub channel the orker publishes to
        pubsub = r.pubsub()
        await pubsub.subscribe("high_risk_flags")
        
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            
            data = message["data"]
            
            # keep a rolling list of recent high risk flags in redis for replays
            await r.lpush("recent_high_risk_flags", data)
            await r.ltrim("recent_high_risk_flags", 0, 19) # keeping only the last 20
            
            #send it to the frontend
            await websocket.send_text(data)
            
    except WebSocketDisconnect:
        log.info("websocket client disconnected")
    except Exception as e:
        log.error(f"websocket error: {e}")
    finally:
        await r.close()
    