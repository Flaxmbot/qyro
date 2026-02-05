package com.qyro.chat;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import qyro.lib.Qyro;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class ChatService {
    private static final Gson gson = new Gson();
    
    public static void main(String[] args) {
        System.out.println("[Java] Starting Chat Service with qyro.lib...");
        
        // Register event handlers
        Qyro.on("user_message", ChatService::handleMessage);
        Qyro.on("typing_broadcast", ChatService::handleTyping);
        
        // Start the event listener
        Qyro.start();
        
        System.out.println("[Java] Service ready!");
    }
    
    private static void handleMessage(String data) {
        try {
            JsonObject json = gson.fromJson(data, JsonObject.class);
            String user = json.has("user") ? json.get("user").getAsString() : "anonymous";
            String message = json.has("message") ? json.get("message").getAsString() : "";
            
            System.out.println("[Java] Received from " + user + ": " + message);
            
            // Emit response
            JsonObject response = new JsonObject();
            response.addProperty("user", user);
            response.addProperty("response", "Java processed: " + message);
            response.addProperty("source", "java");
            
            Qyro.emit("chat_response", gson.toJson(response));
            
        } catch (Exception e) {
            System.err.println("[Java] Error: " + e.getMessage());
        }
    }
    
    private static void handleTyping(String data) {
        try {
            JsonObject json = gson.fromJson(data, JsonObject.class);
            String user = json.has("user") ? json.get("user").getAsString() : "anonymous";
            System.out.println("[Java] " + user + " is typing...");
        } catch (Exception e) {
            System.err.println("[Java] Error: " + e.getMessage());
        }
    }
}