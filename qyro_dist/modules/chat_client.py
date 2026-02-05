from qyro.lib import qyro

@qyro.on("chat_response")
def display_response(data):
    """Display chat responses"""
    print(f"Response: {data.get('response')}")

@qyro.on("typing_status")
def show_typing(data):
    """Show typing status"""
    print(f"User typing: {data.get('user')}")

@qyro.on("user_joined")
def show_join(data):
    """Show user joined notification"""
    print(f"User joined: {data.get('user')}")

@qyro.on("user_left")
def show_leave(data):
    """Show user left notification"""
    print(f"User left: {data.get('user')}")

# Start the event listener
if __name__ == "__main__":
    print("[Python Client] Starting qyro client...")
    qyro.start()