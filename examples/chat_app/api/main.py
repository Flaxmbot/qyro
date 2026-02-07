from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Set
import sys
import json
sys.path.insert(0, '/app/qyro_adapters')
from python_adapter import set as redis_set, get as redis_get, info, expose

app = FastAPI(title="Qyro Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    username: str
    content: str

# In-memory state
messages: List[dict] = []
connected_clients: Set[WebSocket] = set()

@expose
def get_messages():
    """Get all messages - exposed for RPC."""
    return messages

@expose  
def add_message(username: str, content: str):
    """Add a message - exposed for RPC."""
    msg = {"username": username, "content": content}
    messages.append(msg)
    info(f"Message from {username}: {content}")
    return msg

async def broadcast(message: dict):
    """Broadcast to all connected WebSocket clients."""
    for client in connected_clients.copy():
        try:
            await client.send_json(message)
        except:
            connected_clients.discard(client)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.add(ws)
    info(f"WebSocket client connected. Total: {len(connected_clients)}")
    
    try:
        while True:
            data = await ws.receive_json()
            
            if data.get("type") == "get_messages":
                await ws.send_json({"type": "messages", "messages": messages})
            
            elif data.get("type") == "send_message":
                msg = add_message(data["username"], data["content"])
                # Broadcast to all clients
                await broadcast({"type": "new_message", "message": msg})
                
    except WebSocketDisconnect:
        connected_clients.discard(ws)
        info(f"WebSocket client disconnected. Total: {len(connected_clients)}")

@app.get("/")
def root():
    return {"service": "Qyro Chat API", "status": "running", "websocket": "/ws"}

@app.get("/messages")
def list_messages():
    return {"messages": messages}

@app.post("/send")
async def send_message(msg: Message):
    result = add_message(msg.username, msg.content)
    await broadcast({"type": "new_message", "message": result})
    return result

if __name__ == "__main__":
    import uvicorn
    info("Starting Qyro Chat API with WebSocket support on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)