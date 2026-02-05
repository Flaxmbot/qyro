from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import qyro_adapters.python_adapter as qyro

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Msg(BaseModel):
    text: str

@app.post("/send")
def send_msg(msg: Msg):
    qyro.publish("raw_messages", {"user": "User", "text": msg.text})
    return {"status": "ok"}

@app.get("/messages")
def get_msgs():
    # Read from Redis list "chat_history"
    # qyro.get returns value, we need lrange logic.
    # My python adapter only exposes get/set (simple KV).
    # But I can access the underlying redis client.
    r = qyro.Qyro.get_redis()
    msgs = r.lrange("chat_history", 0, -1)
    import json
    return [json.loads(m) for m in msgs]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)