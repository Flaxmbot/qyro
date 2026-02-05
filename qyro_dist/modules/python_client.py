"""
Python Chat Client - Simple CLI client for testing
"""

import asyncio
import redis.asyncio as redis
import json
import os

async def chat_client():
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))
    client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    
    # Subscribe to broadcasts
    pubsub = client.pubsub()
    await pubsub.subscribe("qyro:chat:broadcast")
    
    print("[Python Client] Connected to chat")
    
    # Send a test message
    await client.publish(
        "qyro:chat:python",
        json.dumps({
            "type": "chat",
            "username": "PythonUser",
            "message": "Hello from Python!"
        })
    )
    
    # Listen for broadcasts
    print("[Python Client] Waiting for messages...")
    async for msg in pubsub.listen():
        if msg["type"] == "message":
            data = json.loads(msg["data"])
            print(f"[Broadcast] {data.get('username')}: {data.get('message')}")
            break
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(chat_client())