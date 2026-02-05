"""
Python Chat Server - Main chat orchestration
Handles incoming messages and broadcasts to all connected clients via Redis
"""

import asyncio
import redis.asyncio as redis
import json
import os
from datetime import datetime

# Get Redis host from environment or default to localhost
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

class ChatServer:
    def __init__(self, redis_host=REDIS_HOST, redis_port=REDIS_PORT):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.client = None
        self.pubsub = None
    
    async def start(self):
        """Start the chat server."""
        self.client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True
        )
        
        # Subscribe to all chat channels
        self.pubsub = self.client.pubsub()
        await self.pubsub.subscribe(
            "qyro:chat:python",
            "qyro:chat:react",
            "qyro:chat:rust",
            "qyro:chat:java",
            "qyro:chat:broadcast"
        )
        
        print("[Python] Chat server started on Redis pub/sub")
        
        # Listen for messages
        async for msg in self.pubsub.listen():
            if msg["type"] == "message":
                await self.handle_message(msg)
    
    async def handle_message(self, msg):
        """Process incoming chat messages."""
        channel = msg["channel"]
        data = json.loads(msg["data"])
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        source = channel.split(":")[-1]
        
        print(f"[{timestamp}] [{source.upper()}] {data.get('username', 'User')}: {data.get('message', '')}")
        
        # Broadcast to all channels
        response = {
            "type": "chat",
            "source": "python",
            "username": "Python Server",
            "message": f"Echo from Python: {data.get('message', '')}",
            "timestamp": timestamp
        }
        
        await self.client.publish("qyro:chat:broadcast", json.dumps(response))

async def main():
    server = ChatServer()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())