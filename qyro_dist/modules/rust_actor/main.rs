use qyro_lib::qyro;

#[qyro::handler]
fn handle_chat_message(data: &serde_json::Value) {
    let user = data.get("user").and_then(|u| u.as_str()).unwrap_or("anonymous");
    let message = data.get("message").and_then(|m| m.as_str()).unwrap_or("");
    
    println!("[Rust] Received from {}: {}", user, message);
    
    // Process and emit response
    let response = format!("Rust processed: {}", message);
    qyro::emit("chat_response", serde_json::json!({
        "user": user,
        "response": response,
        "source": "rust"
    }));
}

#[qyro::handler]
fn handle_typing(data: &serde_json::Value) {
    let user = data.get("user").and_then(|u| u.as_str()).unwrap_or("anonymous");
    println!("[Rust] {} is typing...", user);
}

fn main() {
    println!("[Rust] Starting Rust Chat Actor with qyro.lib...");
    
    // Register event handlers
    qyro::on("user_message", handle_chat_message);
    qyro::on("typing_broadcast", handle_typing);
    
    // Start the event listener
    qyro::start();
    
    println!("[Rust] Actor ready!");
}