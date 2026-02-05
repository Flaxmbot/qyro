from qyro.lib import qyro
from datetime import datetime

@qyro.on("user_message")
def handle_message(data):
    """Handle incoming user messages"""
    message = data.get("message", "")
    user = data.get("user", "anonymous")
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    print(f"[{timestamp}] [USER] {user}: {message}")
    
    # Process message and emit response
    response = f"Echo from Python Server: {message}"
    qyro.emit("chat_response", {
        "user": user,
        "response": response,
        "timestamp": timestamp,
        "source": "python"
    })
    return {"status": "processed"}

@qyro.on("typing_broadcast")
def handle_typing(data):
    """Handle typing indicators"""
    user = data.get("user", "anonymous")
    print(f"[TYPING] {user} is typing...")
    qyro.emit("typing_status", data)
    return {"status": "broadcast"}

@qyro.on("user_join")
def handle_user_join(data):
    """Handle user join events"""
    user = data.get("user", "anonymous")
    print(f"[JOIN] {user} joined the chat")
    qyro.emit("user_joined", {"user": user, "timestamp": datetime.now().strftime("%H:%M:%S")})
    return {"status": "broadcast"}

@qyro.on("user_leave")
def handle_user_leave(data):
    """Handle user leave events"""
    user = data.get("user", "anonymous")
    print(f"[LEAVE] {user} left the chat")
    qyro.emit("user_left", {"user": user, "timestamp": datetime.now().strftime("%H:%M:%S")})
    return {"status": "broadcast"}

# Start the event listener
if __name__ == "__main__":
    print("[Python] Chat server starting with qyro.lib...")
    qyro.start()