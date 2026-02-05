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

#include "nexus.h"
#include <hiredis/hiredis.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdarg.h>

#ifdef _WIN32
#include <windows.h>
#include <process.h>
#define getpid _getpid
#else
#include <unistd.h>
#endif

/* ============================================================================
 * GLOBALS
 * ============================================================================ */

static NexusContext* g_nexus = NULL;

/* ============================================================================
 * INITIALIZATION
 * ============================================================================ */

/**
 * Load Redis configuration from environment variables.
 */
static void nexus_load_config(NexusRedisConfig* config) {
    const char* host = getenv("NEXUS_REDIS_HOST");
    const char* port = getenv("NEXUS_REDIS_PORT");
    const char* db = getenv("NEXUS_REDIS_DB");
    const char* password = getenv("NEXUS_REDIS_PASSWORD");
    const char* module_name = getenv("NEXUS_MODULE_NAME");

    strncpy(config->host, host ? host : "localhost", sizeof(config->host) - 1);
    config->port = port ? atoi(port) : 6379;
    config->db = db ? atoi(db) : 0;
    strncpy(config->password, password ? password : "", sizeof(config->password) - 1);
    strncpy(config->module_name, module_name ? module_name : "c_module",
            sizeof(config->module_name) - 1);
}

/**
 * Generate a unique process ID.
 */
static void nexus_generate_process_id(char* pid, size_t len) {
    unsigned int seed = (unsigned int)time(NULL) ^ (unsigned int)getpid();
    srand(seed);
    snprintf(pid, len, "%08x", rand());
}

/**
 * Logging levels
 */
typedef enum {
    LOG_DEBUG = 0,
    LOG_INFO = 1,
    LOG_WARN = 2,
    LOG_ERROR = 3
} LogLevel;

/**
 * Log a message with timestamp and level
 */
static void nexus_log(LogLevel level, const char* format, ...) {
    time_t now;
    time(&now);
    char* time_str = ctime(&now);
    // Remove newline from ctime result
    time_str[strlen(time_str)-1] = '\0';

    const char* level_str;
    switch(level) {
        case LOG_DEBUG: level_str = "DEBUG"; break;
        case LOG_INFO:  level_str = "INFO "; break;
        case LOG_WARN:  level_str = "WARN "; break;
        case LOG_ERROR: level_str = "ERROR"; break;
        default:        level_str = "UNKWN"; break;
    }

    va_list args;
    va_start(args, format);
    printf("[%s] [%s] [%s] ", time_str, level_str, g_nexus ? g_nexus->process_id : "unknown");
    vprintf(format, args);
    printf("\n");
    fflush(stdout);
    va_end(args);
}

/**
 * Log an RPC call
 */
static void log_rpc_call(const char* function_name, const char* caller, int success) {
    if (success) {
        nexus_log(LOG_INFO, "RPC_CALL_SUCCESS: function=%s, caller=%s", function_name, caller);
    } else {
        nexus_log(LOG_ERROR, "RPC_CALL_FAILED: function=%s, caller=%s", function_name, caller);
    }
}

/**
 * Log a state operation
 */
static void log_state_operation(const char* operation, const char* key, int success) {
    if (success) {
        nexus_log(LOG_INFO, "STATE_%s_SUCCESS: key=%s", operation, key ? key : "(all)");
    } else {
        nexus_log(LOG_ERROR, "STATE_%s_FAILED: key=%s", operation, key ? key : "(all)");
    }
}

/**
 * Initialize circuit breaker
 */
static void init_circuit_breaker(CircuitBreaker* cb) {
    cb->state = CB_CLOSED;
    cb->failure_count = 0;
    cb->last_failure_time = 0;
    cb->last_attempt_time = 0;
}

/**
 * Check if circuit breaker allows operation
 */
static int circuit_breaker_allows_operation(CircuitBreaker* cb) {
    if (cb->state == CB_OPEN) {
        // Check if enough time has passed to try again
        if (difftime(time(NULL), cb->last_failure_time) >= CIRCUIT_BREAKER_RESET_TIMEOUT) {
            cb->state = CB_HALF_OPEN;
            return 1; // Allow one trial operation
        }
        return 0; // Still in open state, reject operation
    }
    return 1; // Closed or half-open, allow operation
}

/**
 * Record a successful operation
 */
static void circuit_breaker_record_success(CircuitBreaker* cb) {
    cb->state = CB_CLOSED;
    cb->failure_count = 0;
    cb->last_attempt_time = time(NULL);
}

/**
 * Record a failed operation
 */
static void circuit_breaker_record_failure(CircuitBreaker* cb) {
    cb->failure_count++;
    cb->last_failure_time = time(NULL);
    cb->last_attempt_time = time(NULL);

    // Open the circuit if threshold is exceeded
    if (cb->failure_count >= CIRCUIT_BREAKER_FAILURE_THRESHOLD) {
        cb->state = CB_OPEN;
    }
}

/**
 * Initialize connection to Redis.
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_init(void) {
    if (g_nexus != NULL) {
        return NEXUS_OK; // Already initialized
    }

    NexusRedisConfig config;
    nexus_load_config(&config);

    // Allocate context
    g_nexus = (NexusContext*)calloc(1, sizeof(NexusContext));
    if (g_nexus == NULL) {
        return NEXUS_ERR_REDIS_CONNECTION_FAILED;
    }

    // Initialize circuit breakers
    init_circuit_breaker(&g_nexus->rpc_circuit_breaker);
    init_circuit_breaker(&g_nexus->state_circuit_breaker);
    init_circuit_breaker(&g_nexus->event_circuit_breaker);

    // Generate process ID
    nexus_generate_process_id(g_nexus->process_id, sizeof(g_nexus->process_id));
    strncpy(g_nexus->module_name, config.module_name, sizeof(g_nexus->module_name) - 1);

    // Connect to Redis
    struct timeval timeout = { 1, 500000 }; // 1.5 seconds
    g_nexus->redis = redisConnectWithTimeout(config.host, config.port, timeout);

    if (g_nexus->redis == NULL || g_nexus->redis->err) {
        if (g_nexus->redis) {
            printf("[NEXUS-C] Connection error: %s\n", g_nexus->redis->errstr);
            redisFree(g_nexus->redis);
        } else {
            printf("[NEXUS-C] Connection error: can't allocate redis context\n");
        }
        free(g_nexus);
        g_nexus = NULL;
        return NEXUS_ERR_REDIS_CONNECTION_FAILED;
    }

    // Authenticate if password provided
    if (strlen(config.password) > 0) {
        redisReply* reply = redisCommand(g_nexus->redis, "AUTH %s", config.password);
        if (reply == NULL || reply->type == REDIS_REPLY_ERROR) {
            printf("[NEXUS-C] Authentication failed\n");
            if (reply) freeReplyObject(reply);
            redisFree(g_nexus->redis);
            free(g_nexus);
            g_nexus = NULL;
            return NEXUS_ERR_REDIS_CONNECTION_FAILED;
        }
        freeReplyObject(reply);
    }

    // Select database
    if (config.db != 0) {
        redisReply* reply = redisCommand(g_nexus->redis, "SELECT %d", config.db);
        if (reply) freeReplyObject(reply);
    }

    // Test connection
    redisReply* reply = redisCommand(g_nexus->redis, "PING");
    if (reply == NULL || reply->type == REDIS_REPLY_ERROR) {
        printf("[NEXUS-C] PING failed\n");
        if (reply) freeReplyObject(reply);
        redisFree(g_nexus->redis);
        free(g_nexus);
        g_nexus = NULL;
        return NEXUS_ERR_REDIS_CONNECTION_FAILED;
    }
    freeReplyObject(reply);

    printf("[NEXUS-C] Connected to Redis at %s:%d\n", config.host, config.port);
    printf("[NEXUS-C] Module: %s (PID: %s)\n", config.module_name, g_nexus->process_id);

    return NEXUS_OK;
}

/**
 * Cleanup and disconnect from Redis.
 */
void nexus_cleanup(void) {
    if (g_nexus == NULL) return;

    g_nexus->running = 0;

    if (g_nexus->subscriber) {
        redisFree(g_nexus->subscriber);
        g_nexus->subscriber = NULL;
    }

    if (g_nexus->redis) {
        redisFree(g_nexus->redis);
        g_nexus->redis = NULL;
    }

    free(g_nexus);
    g_nexus = NULL;

    printf("[NEXUS-C] Disconnected from Redis\n");
}

/* ============================================================================
 * STATE OPERATIONS
 * ============================================================================ */

/**
 * Read the current state from Redis.
 * @return Allocated JSON string (caller must free), or NULL on error
 */
char* nexus_read_state(void) {
    if (g_nexus == NULL || g_nexus->redis == NULL) {
        return strdup("{}");
    }

    // Use HGETALL to get all fields from the hash
    redisReply* reply = redisCommand(g_nexus->redis, "HGETALL %s", CHANNEL_STATE);
    if (reply == NULL || reply->type == REDIS_REPLY_ERROR) {
        if (reply) freeReplyObject(reply);
        return strdup("{}");
    }

    // Convert hash to JSON string
    if (reply->type == REDIS_REPLY_ARRAY && reply->elements > 0) {
        // Build JSON object from hash
        size_t json_capacity = 4096; // Start with 4KB capacity
        char* json_result = malloc(json_capacity);
        if (!json_result) {
            freeReplyObject(reply);
            return strdup("{}");
        }

        strcpy(json_result, "{");
        size_t current_len = 1;

        for (size_t i = 0; i < reply->elements; i += 2) {
            char* key = reply->element[i]->str;
            char* value = reply->element[i+1]->str;

            // Skip the "state" field if it exists, as we want to return individual fields
            // This maintains consistency with other adapters that store individual fields
            if (strcmp(key, "state") == 0) {
                continue;
            }

            if (i > 0 && current_len > 1) { // Only add comma if not the first element
                strcat(json_result, ",");
                current_len++;
            }

            // Calculate needed space (with quotes and colon)
            size_t needed = current_len + strlen(key) + strlen(value) + 6; // +6 for quotes, colon, quotes, comma

            // Expand buffer if needed
            if (needed > json_capacity) {
                json_capacity = needed + 1024; // Add extra space
                char* temp = realloc(json_result, json_capacity);
                if (!temp) {
                    free(json_result);
                    freeReplyObject(reply);
                    return strdup("{}");
                }
                json_result = temp;
            }

            // Add key-value pair to JSON
            int written = snprintf(json_result + current_len,
                                  json_capacity - current_len,
                                  "\"%s\":\"%s\"",
                                  key, value);
            if (written < 0 || written >= (int)(json_capacity - current_len)) {
                // Handle error - snprintf failed
                free(json_result);
                freeReplyObject(reply);
                return strdup("{}");
            }
            current_len += written;
        }

        strcat(json_result, "}");
        freeReplyObject(reply);
        return json_result;
    } else {
        freeReplyObject(reply);
        return strdup("{}");
    }
}

/**
 * Helper function to parse simple JSON objects and store individual fields in Redis hash
 * This is a simplified implementation - in production, use a proper JSON parser like cJSON
 */
static NexusErrorCode parse_and_store_json_fields(redisContext* ctx, const char* json_str) {
    // This is a very basic JSON parser that handles simple key-value pairs
    // Format: {"key1":"value1","key2":"value2"}

    if (!json_str) return NEXUS_ERR_JSON_PARSE;
    size_t len = strlen(json_str);
    if (len < 2) return NEXUS_OK; // Empty object

    // Skip opening brace
    const char* ptr = json_str;
    if (*ptr == '{') ptr++;

    // Remove trailing brace if present
    size_t remaining_len = strlen(ptr);
    if (remaining_len == 0) return NEXUS_OK;

    char* temp_json = malloc(remaining_len + 1);
    if (!temp_json) return NEXUS_ERR_JSON_PARSE;

    strcpy(temp_json, ptr);

    // Remove trailing brace
    if (temp_json[remaining_len-1] == '}') {
        temp_json[remaining_len-1] = '\0';
    }

    // Parse key-value pairs
    char* token = strtok(temp_json, ",");
    while (token != NULL) {
        // Find key and value in format: "key":"value"
        char* colon_pos = strchr(token, ':');
        if (colon_pos != NULL) {
            *colon_pos = '\0'; // Split at colon

            char* key = token;
            char* value = colon_pos + 1;

            // Remove quotes from key
            while (*key == ' ' || *key == '"') key++;
            char* end_key = key + strlen(key) - 1;
            while (end_key >= key && (*end_key == ' ' || *end_key == '"')) {
                *end_key = '\0';
                end_key--;
            }

            // Remove quotes from value
            while (*value == ' ' || *value == '"') value++;
            char* end_value = value + strlen(value) - 1;
            while (end_value >= value && (*end_value == ' ' || *end_value == '"')) {
                *end_value = '\0';
                end_value--;
            }

            // Validate key is not empty
            if (strlen(key) == 0) {
                token = strtok(NULL, ",");
                continue; // Skip empty keys
            }

            // Store in Redis hash
            redisReply* reply = redisCommand(ctx, "HSET %s %s %s", CHANNEL_STATE, key, value);
            if (reply) {
                if (reply->type == REDIS_REPLY_ERROR) {
                    freeReplyObject(reply);
                    free(temp_json);
                    return NEXUS_ERR_STATE_WRITE_FAILED;
                }
                freeReplyObject(reply);
            }
        }
        token = strtok(NULL, ",");
    }

    free(temp_json);
    return NEXUS_OK;
}

/**
 * Write state to Redis and publish state change notification.
 * @param json JSON string to write
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_write_state(const char* json) {
    if (g_nexus == NULL || g_nexus->redis == NULL) {
        nexus_log(LOG_ERROR, "nexus_write_state: Invalid context or Redis connection");
        return NEXUS_ERR_STATE_WRITE_FAILED;
    }

    // Check circuit breaker
    if (!circuit_breaker_allows_operation(&g_nexus->state_circuit_breaker)) {
        nexus_log(LOG_WARN, "State circuit breaker OPEN - rejecting write operation");
        return NEXUS_ERR_CIRCUIT_OPEN;
    }

    // Parse the JSON and store individual fields for consistency with other adapters
    // This maintains compatibility while ensuring all adapters use the same storage format
    NexusErrorCode result = parse_and_store_json_fields(g_nexus->redis, json);

    if (result != NEXUS_OK) {
        circuit_breaker_record_failure(&g_nexus->state_circuit_breaker);
        nexus_log(LOG_ERROR, "nexus_write_state: Failed to parse and store JSON fields");
        return result;
    }

    circuit_breaker_record_success(&g_nexus->state_circuit_breaker);

    // Publish state change notification
    char notification[512];
    snprintf(notification, sizeof(notification),
             "{\"module\":\"%s\",\"pid\":\"%s\",\"timestamp\":%f}",
             g_nexus->module_name, g_nexus->process_id,
             (double)time(NULL));

    redisReply* reply = redisCommand(g_nexus->redis, "PUBLISH %s %s",
                        CHANNEL_STATE_CHANGED, notification);
    if (reply) freeReplyObject(reply);

    nexus_log(LOG_INFO, "nexus_write_state: Successfully wrote state to Redis");
    return NEXUS_OK;
}

/**
 * Write a specific field to the state hash.
 * @param field Field name
 * @param value Field value (JSON string)
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_write_field(const char* field, const char* value) {
    if (g_nexus == NULL || g_nexus->redis == NULL) {
        return NEXUS_ERR_STATE_WRITE_FAILED;
    }

    redisReply* reply = redisCommand(g_nexus->redis, "HSET %s %s %s", 
                                   CHANNEL_STATE, field, value);
    if (reply == NULL || reply->type == REDIS_REPLY_ERROR) {
        if (reply) freeReplyObject(reply);
        return NEXUS_ERR_STATE_WRITE_FAILED;
    }
    freeReplyObject(reply);

    // Publish state change notification
    char notification[512];
    snprintf(notification, sizeof(notification),
             "{\"module\":\"%s\",\"pid\":\"%s\",\"field\":\"%s\",\"timestamp\":%f}",
             g_nexus->module_name, g_nexus->process_id, field,
             (double)time(NULL));

    reply = redisCommand(g_nexus->redis, "PUBLISH %s %s",
                        CHANNEL_STATE_CHANGED, notification);
    if (reply) freeReplyObject(reply);

    return NEXUS_OK;
}

/**
 * Read a specific field from the state hash.
 * @param field Field name to read
 * @return Allocated JSON string (caller must free), or NULL on error
 */
char* nexus_read_field(const char* field) {
    if (g_nexus == NULL || g_nexus->redis == NULL) {
        return NULL;
    }

    redisReply* reply = redisCommand(g_nexus->redis, "HGET %s %s", CHANNEL_STATE, field);
    if (reply == NULL || reply->type == REDIS_REPLY_ERROR) {
        if (reply) freeReplyObject(reply);
        return NULL;
    }

    char* result = NULL;
    if (reply->type == REDIS_REPLY_STRING) {
        result = strndup(reply->str, reply->len);
    }

    freeReplyObject(reply);
    return result;
}

/* ============================================================================
 * EVENT OPERATIONS
 * ============================================================================ */

/**
 * Publish an event to the events channel.
 * @param event_type Type of event
 * @param data JSON string containing event data
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_publish_event(const char* event_type, const char* data) {
    if (g_nexus == NULL || g_nexus->redis == NULL) {
        return NEXUS_ERR_EVENT_PUBLISH_FAILED;
    }

    char event[1024];
    snprintf(event, sizeof(event),
             "{\"type\":\"%s\",\"module\":\"%s\",\"pid\":\"%s\",\"timestamp\":%f,\"data\":%s}",
             event_type, g_nexus->module_name, g_nexus->process_id,
             (double)time(NULL), data);

    redisReply* reply = redisCommand(g_nexus->redis, "PUBLISH %s %s",
                        CHANNEL_EVENTS, event);
    if (reply == NULL || reply->type == REDIS_REPLY_ERROR) {
        if (reply) freeReplyObject(reply);
        return NEXUS_ERR_EVENT_PUBLISH_FAILED;
    }
    freeReplyObject(reply);

    return NEXUS_OK;
}

/**
 * Broadcast a message to all modules.
 * @param message JSON string containing message
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_broadcast(const char* message) {
    if (g_nexus == NULL || g_nexus->redis == NULL) {
        return NEXUS_ERR_EVENT_PUBLISH_FAILED;
    }

    char broadcast_msg[1024];
    snprintf(broadcast_msg, sizeof(broadcast_msg),
             "{\"module\":\"%s\",\"pid\":\"%s\",\"timestamp\":%f,\"message\":%s}",
             g_nexus->module_name, g_nexus->process_id,
             (double)time(NULL), message);

    redisReply* reply = redisCommand(g_nexus->redis, "PUBLISH %s %s",
                        CHANNEL_BROADCAST, broadcast_msg);
    if (reply == NULL || reply->type == REDIS_REPLY_ERROR) {
        if (reply) freeReplyObject(reply);
        return NEXUS_ERR_EVENT_PUBLISH_FAILED;
    }
    freeReplyObject(reply);

    return NEXUS_OK;
}

/* ============================================================================
 * SUBSCRIPTION HANDLERS
 * ============================================================================ */

/**
 * Register an event handler.
 * @param handler Function to call when event is received
 */
void nexus_on_event(void (*handler)(const char* channel, const char* message)) {
    if (g_nexus) {
        g_nexus->event_handler = handler;
    }
}

/**
 * Register a state change handler.
 * @param handler Function to call when state changes
 */
void nexus_on_state_changed(void (*handler)(const char* message)) {
    if (g_nexus) {
        g_nexus->state_change_handler = handler;
    }
}

/**
 * Register a broadcast handler.
 * @param handler Function to call when broadcast is received
 */
void nexus_on_broadcast(void (*handler)(const char* message)) {
    if (g_nexus) {
        g_nexus->broadcast_handler = handler;
    }
}

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
NexusErrorCode nexus_subscribe(void) {
    if (g_nexus == NULL || g_nexus->redis == NULL) {
        return NEXUS_ERR_REDIS_SUBSCRIPTION_FAILED;
    }

    // Create subscriber connection
    NexusRedisConfig config;
    nexus_load_config(&config);

    struct timeval timeout = { 1, 500000 };
    g_nexus->subscriber = redisConnectWithTimeout(config.host, config.port, timeout);

    if (g_nexus->subscriber == NULL || g_nexus->subscriber->err) {
        if (g_nexus->subscriber) {
            printf("[NEXUS-C] Subscriber connection error: %s\n", g_nexus->subscriber->errstr);
            redisFree(g_nexus->subscriber);
        }
        g_nexus->subscriber = NULL;
        return NEXUS_ERR_REDIS_SUBSCRIPTION_FAILED;
    }

    // Authenticate if password provided
    if (strlen(config.password) > 0) {
        redisReply* reply = redisCommand(g_nexus->subscriber, "AUTH %s", config.password);
        if (reply) freeReplyObject(reply);
    }

    // Select database
    if (config.db != 0) {
        redisReply* reply = redisCommand(g_nexus->subscriber, "SELECT %d", config.db);
        if (reply) freeReplyObject(reply);
    }

    // Subscribe to channels
    redisReply* reply = redisCommand(g_nexus->subscriber, "SUBSCRIBE %s %s %s",
                                   CHANNEL_STATE_CHANGED, CHANNEL_EVENTS, CHANNEL_BROADCAST);
    if (reply == NULL || reply->type == REDIS_REPLY_ERROR) {
        if (reply) freeReplyObject(reply);
        redisFree(g_nexus->subscriber);
        g_nexus->subscriber = NULL;
        return NEXUS_ERR_REDIS_SUBSCRIPTION_FAILED;
    }
    freeReplyObject(reply);

    g_nexus->subscribed = 1;
    g_nexus->running = 1;

    printf("[NEXUS-C] Subscribed to Redis channels\n");

    return NEXUS_OK;
}

/**
 * Process incoming messages (blocking call).
 * This should be called in a separate thread or in a loop.
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_process_messages(void) {
    if (g_nexus == NULL || g_nexus->subscriber == NULL) {
        return NEXUS_ERR_REDIS_SUBSCRIPTION_FAILED;
    }

    // Use redisGetReply to get messages from subscription
    while (g_nexus->running) {
        void* reply_ptr = NULL;
        int status = redisGetReply(g_nexus->subscriber, &reply_ptr);
        
        if (status != REDIS_OK || reply_ptr == NULL) {
#ifdef _WIN32
            Sleep(100);
#else
            usleep(100000); // 100ms
#endif
            continue;
        }

        redisReply* reply = (redisReply*)reply_ptr;

        if (reply->type == REDIS_REPLY_ARRAY && reply->elements >= 3) {
            // Message format: [type, channel, payload] or [type, channel, pattern, payload]
            char* msg_type = reply->element[0]->str;
            char* channel = reply->element[1]->str;
            char* payload = NULL;
            
            // Determine if this is a message with pattern (4 elements) or without (3 elements)
            if (reply->elements == 4) {
                payload = reply->element[3]->str; // Format: [type, pattern, channel, payload]
            } else {
                payload = reply->element[2]->str; // Format: [type, channel, payload]
            }

            // Dispatch to appropriate handler
            if (strcmp(msg_type, "message") == 0) {
                if (strcmp(channel, CHANNEL_STATE_CHANGED) == 0) {
                    if (g_nexus->state_change_handler) {
                        g_nexus->state_change_handler(payload);
                    }
                } else if (strcmp(channel, CHANNEL_EVENTS) == 0) {
                    if (g_nexus->event_handler) {
                        g_nexus->event_handler(channel, payload);
                    }
                } else if (strcmp(channel, CHANNEL_BROADCAST) == 0) {
                    if (g_nexus->broadcast_handler) {
                        g_nexus->broadcast_handler(payload);
                    }
                }
            }
        }

        freeReplyObject(reply);
    }

    return NEXUS_OK;
}

/* ============================================================================
 * RPC SUPPORT
 * ============================================================================ */

/**
 * Register a function for cross-language RPC calls.
 * @param name Function name
 * @return NEXUS_OK on success, error code on failure
 */
NexusErrorCode nexus_register_function(const char* name) {
    if (g_nexus == NULL || g_nexus->redis == NULL) {
        return NEXUS_ERR_EVENT_PUBLISH_FAILED;
    }

    char registration[512];
    snprintf(registration, sizeof(registration),
             "{\"type\":\"function_register\",\"name\":\"%s\",\"module\":\"%s\",\"pid\":\"%s\",\"lang\":\"c\"}",
             name, g_nexus->module_name, g_nexus->process_id);

    return nexus_publish_event("function_register", registration);
}

/**
 * Call a function registered in another module.
 * @param name Function name
 * @param args_json JSON string containing arguments
 * @param timeout_ms Timeout in milliseconds
 * @return Allocated JSON result string (caller must free), or NULL on error
 */
char* nexus_call_function(const char* name, const char* args_json, int timeout_ms) {
    if (g_nexus == NULL || g_nexus->redis == NULL) {
        return NULL;
    }

    // Check circuit breaker
    if (!circuit_breaker_allows_operation(&g_nexus->rpc_circuit_breaker)) {
        printf("[NEXUS-C] RPC circuit breaker OPEN - rejecting call to %s\n", name);
        return NULL;
    }

    char call_id[32];
    nexus_generate_process_id(call_id, sizeof(call_id));

    char call_request[1024];
    snprintf(call_request, sizeof(call_request),
             "{\"id\":\"%s\",\"fn\":\"%s\",\"args\":%s,\"caller\":\"%s\",\"timestamp\":%f}",
             call_id, name, args_json, g_nexus->process_id, (double)time(NULL));

    // Publish function call event
    NexusErrorCode pub_result = nexus_publish_event("function_call", call_request);
    if (pub_result != NEXUS_OK) {
        circuit_breaker_record_failure(&g_nexus->rpc_circuit_breaker);
        return NULL;
    }

    // Create result channel for this specific call using pub/sub
    char result_channel[64];
    snprintf(result_channel, sizeof(result_channel), "nexus:rpc:result:%s", call_id);

    // Use existing redis connection for pubsub instead of creating new one
    // Create a temporary pubsub connection to listen for the result
    NexusRedisConfig config;
    nexus_load_config(&config);

    // Use the same connection context but for pubsub operations
    redisContext* pubsub_redis = redisConnectWithTimeout(config.host, config.port, (struct timeval){1, 500000});

    if (pubsub_redis == NULL || pubsub_redis->err) {
        if (pubsub_redis) {
            redisFree(pubsub_redis);
        }
        circuit_breaker_record_failure(&g_nexus->rpc_circuit_breaker);
        return NULL;
    }

    // Authenticate if password provided
    if (strlen(config.password) > 0) {
        redisReply* auth_reply = redisCommand(pubsub_redis, "AUTH %s", config.password);
        if (auth_reply) freeReplyObject(auth_reply);
    }

    // Select database
    if (config.db != 0) {
        redisReply* select_reply = redisCommand(pubsub_redis, "SELECT %d", config.db);
        if (select_reply) freeReplyObject(select_reply);
    }

    // Subscribe to the result channel
    redisReply* sub_reply = redisCommand(pubsub_redis, "SUBSCRIBE %s", result_channel);
    if (sub_reply == NULL || sub_reply->type == REDIS_REPLY_ERROR) {
        if (sub_reply) freeReplyObject(sub_reply);
        redisFree(pubsub_redis);
        circuit_breaker_record_failure(&g_nexus->rpc_circuit_breaker);
        return NULL;
    }
    freeReplyObject(sub_reply);

    // Wait for response with timeout using pub/sub
    time_t start = time(NULL);
    time_t timeout_sec = timeout_ms / 1000;
    if (timeout_sec == 0) timeout_sec = 1; // Minimum 1 second timeout

    char* result = NULL;
    int found_result = 0;

    while (time(NULL) - start < timeout_sec && !found_result) {
        void* reply_ptr = NULL;
        int status = redisGetReply(pubsub_redis, &reply_ptr);

        if (status != REDIS_OK || reply_ptr == NULL) {
#ifdef _WIN32
            Sleep(10);
#else
            usleep(10000); // 10ms
#endif
            continue;
        }

        redisReply* reply = (redisReply*)reply_ptr;

        if (reply->type == REDIS_REPLY_ARRAY && reply->elements >= 3) {
            char* msg_type = reply->element[0]->str;
            char* channel = reply->element[1]->str;
            char* payload = reply->element[2]->str;

            // Check if this is a message from our result channel
            if (strcmp(msg_type, "message") == 0 && strcmp(channel, result_channel) == 0) {
                // Parse the payload to extract the result
                // Simplified parsing - in production, use a proper JSON parser
                // Looking for: {"id":"...","status":2,"result":"..."} or similar
                result = strndup(payload, strlen(payload));
                found_result = 1;
                circuit_breaker_record_success(&g_nexus->rpc_circuit_breaker);
            }
        }

        freeReplyObject(reply);
    }

    // If no result found within timeout, record failure
    if (!found_result) {
        circuit_breaker_record_failure(&g_nexus->rpc_circuit_breaker);
    }

    // Clean up
    redisCommand(pubsub_redis, "UNSUBSCRIBE %s", result_channel);
    redisFree(pubsub_redis);

    return result;
}

/* ============================================================================
 * GETTERS
 * ============================================================================ */

/**
 * Get process ID.
 */
const char* nexus_get_process_id(void) {
    return g_nexus ? g_nexus->process_id : "";
}

/**
 * Get module name.
 */
const char* nexus_get_module_name(void) {
    return g_nexus ? g_nexus->module_name : "";
}

/**
 * Check if connected to Redis.
 */
int nexus_is_connected(void) {
    return g_nexus != NULL && g_nexus->redis != NULL && g_nexus->redis->err == 0;
}

/**
 * Check if subscribed to channels.
 */
int nexus_is_subscribed(void) {
    return g_nexus != NULL && g_nexus->subscribed;
}