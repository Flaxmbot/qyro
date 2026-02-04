#ifndef NEXUS_H
#define NEXUS_H

/**
 * Nexus C Adapter - Redis Pub/Sub Implementation
 * Thread-safe Redis-based communication for cross-language integration.
 *
 * This adapter uses Redis pub/sub for real-time communication instead of
 * file-based shared memory. It reads Redis connection info from environment
 * variables provided by the orchestrator.
 *
 * Environment Variables:
 *     NEXUS_REDIS_HOST - Redis server host (default: localhost)
 *     NEXUS_REDIS_PORT - Redis server port (default: 6379)
 *     NEXUS_REDIS_DB - Redis database number (default: 0)
 *     NEXUS_REDIS_PASSWORD - Redis password (optional)
 *     NEXUS_MODULE_NAME - Module name for this adapter (required)
 *
 * Redis Channels:
 *     nexus:state - Read/write state
 *     nexus:state:changed - Subscribe to state changes
 *     nexus:events - Publish/subscribe to events
 *     nexus:broadcast - Broadcast messages
 *
 * Dependencies:
 *     hiredis (Redis client for C)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#include <process.h>
#define getpid _getpid
#else
#include <unistd.h>
#endif

/* Include hiredis */
#include <hiredis/hiredis.h>

/* ============================================================================
 * CONSTANTS
 * ============================================================================ */

// Redis channel names
#define CHANNEL_STATE "nexus:state"
#define CHANNEL_STATE_CHANGED "nexus:state:changed"
#define CHANNEL_EVENTS "nexus:events"
#define CHANNEL_BROADCAST "nexus:broadcast"

// Circuit breaker constants
#define CIRCUIT_BREAKER_FAILURE_THRESHOLD 5
#define CIRCUIT_BREAKER_RESET_TIMEOUT 30  // seconds

// Error codes matching Python errors.py and constants.py
typedef enum {
    NEXUS_OK = 0,
    NEXUS_ERR_REDIS_CONNECTION_FAILED = 1001,
    NEXUS_ERR_REDIS_SUBSCRIPTION_FAILED = 1002,
    NEXUS_ERR_STATE_READ_FAILED = 1003,
    NEXUS_ERR_STATE_WRITE_FAILED = 1004,
    NEXUS_ERR_EVENT_PUBLISH_FAILED = 1005,
    NEXUS_ERR_JSON_PARSE = 2001,
    NEXUS_ERR_CIRCUIT_OPEN = 3001  // Circuit breaker is open
} NexusErrorCode;

/* ============================================================================
 * TYPES
 * ============================================================================ */

/**
 * Redis connection configuration
 */
typedef struct {
    char host[256];
    int port;
    int db;
    char password[256];
    char module_name[256];
} NexusRedisConfig;

/**
 * Nexus Redis context
 */
typedef struct {
    redisContext* redis;           // Redis client for commands
    redisContext* subscriber;       // Redis client for subscriptions
    char process_id[16];
    char module_name[256];
    int subscribed;
    int running;

    // Event handlers (simplified - in production use proper callback registration)
    void (*event_handler)(const char* channel, const char* message);
    void (*state_change_handler)(const char* message);
    void (*broadcast_handler)(const char* message);
} NexusContext;

/* ============================================================================
 * INITIALIZATION
 * ============================================================================ */

/**
 * Initialize connection to Redis.
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_init(void);

/**
 * Cleanup and disconnect from Redis.
 */
void nexus_cleanup(void);

/* ============================================================================
 * STATE OPERATIONS
 * ============================================================================ */

/**
 * Read the current state from Redis.
 * @return Allocated JSON string (caller must free), or NULL on error
 */
char* nexus_read_state(void);

/**
 * Write state to Redis and publish state change notification.
 * @param json JSON string to write
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_write_state(const char* json);

/**
 * Write a specific field to the state hash.
 * @param field Field name
 * @param value Field value (JSON string)
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_write_field(const char* field, const char* value);

/**
 * Read a specific field from the state hash.
 * @param field Field name to read
 * @return Allocated JSON string (caller must free), or NULL on error
 */
char* nexus_read_field(const char* field);

/* ============================================================================
 * EVENT OPERATIONS
 * ============================================================================ */

/**
 * Publish an event to the events channel.
 * @param event_type Type of event
 * @param data JSON string containing event data
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_publish_event(const char* event_type, const char* data);

/**
 * Broadcast a message to all modules.
 * @param message JSON string containing message
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_broadcast(const char* message);

/* ============================================================================
 * SUBSCRIPTION HANDLERS
 * ============================================================================ */

/**
 * Register an event handler.
 * @param handler Function to call when event is received
 */
void nexus_on_event(void (*handler)(const char* channel, const char* message));

/**
 * Register a state change handler.
 * @param handler Function to call when state changes
 */
void nexus_on_state_changed(void (*handler)(const char* message));

/**
 * Register a broadcast handler.
 * @param handler Function to call when broadcast is received
 */
void nexus_on_broadcast(void (*handler)(const char* message));

/* ============================================================================
 * PUB/SUB LISTENER
 * ============================================================================ */

/**
 * Subscribe to Redis channels and start listening.
 * This subscribes to:
 * - nexus:state:changed - State change notifications
 * - nexus:events - All events
 * - nexus:broadcast - Broadcast messages
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_subscribe(void);

/**
 * Process incoming messages (blocking call).
 * This should be called in a separate thread or in a loop.
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_process_messages(void);

/* ============================================================================
 * RPC SUPPORT
 * ============================================================================ */

/**
 * Register a function for cross-language RPC calls.
 * @param name Function name
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_register_function(const char* name);

/**
 * Call a function registered in another module.
 * @param name Function name
 * @param args_json JSON string containing arguments
 * @param timeout_ms Timeout in milliseconds
 * @return Allocated JSON result string (caller must free), or NULL on error
 */
char* nexus_call_function(const char* name, const char* args_json, int timeout_ms);

/* ============================================================================
 * GETTERS
 * ============================================================================ */

/**
 * Get process ID.
 */
const char* nexus_get_process_id(void);

/**
 * Get module name.
 */
const char* nexus_get_module_name(void);

/**
 * Check if connected to Redis.
 */
int nexus_is_connected(void);

/**
 * Check if subscribed to channels.
 */
int nexus_is_subscribed(void);

#endif /* NEXUS_H */
