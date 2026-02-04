/**
 * Nexus C Function Exports - Redis Pub/Sub Implementation
 * Macros and utilities for registering C functions for cross-language calling.
 * 
 * This header provides macros and utilities for registering C functions
 * that can be called from other languages via Redis pub/sub.
 */

#ifndef NEXUS_EXPORT_H
#define NEXUS_EXPORT_H

#include "nexus.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ============================================================================
 * Constants
 * ============================================================================ */

#define MAX_EXPORTED_FUNCTIONS 64
#define MAX_FUNCTION_NAME_LEN 64
#define MAX_PENDING_CALLS 32

/* Call status codes */
typedef enum {
    NEXUS_CALL_PENDING = 0,
    NEXUS_CALL_PROCESSING = 1,
    NEXUS_CALL_COMPLETED = 2,
    NEXUS_CALL_FAILED = 3,
    NEXUS_CALL_TIMEOUT = 4,
    NEXUS_CALL_CANCELLED = 5
} NexusCallStatus;

/* ============================================================================
 * Types
 * ============================================================================ */

/* Generic function pointer that takes JSON args and returns JSON result */
typedef char* (*NexusExportedFunction)(const char* args_json);

/* Function info stored in registry */
typedef struct {
    char name[MAX_FUNCTION_NAME_LEN];
    NexusExportedFunction handler;
    char param_types[256];
    char return_type[64];
    int registered;
} NexusFunctionEntry;

/* Pending call from queue */
typedef struct {
    char call_id[16];
    char function_name[MAX_FUNCTION_NAME_LEN];
    char* args_json;
    NexusCallStatus status;
    char* result_json;
    char* error;
} NexusPendingCall;

/* ============================================================================
 * Globals
 * ============================================================================ */

__attribute__((unused)) static NexusFunctionEntry nexus_functions[MAX_EXPORTED_FUNCTIONS];
__attribute__((unused)) static int nexus_function_count = 0;
__attribute__((unused)) static char nexus_process_id[16] = "";

/* ============================================================================
 * Export Macros
 * ============================================================================ */

/**
 * NEXUS_EXPORT - Register a function for cross-language calling.
 * 
 * Usage:
 *   char* my_function(const char* args_json) {
 *       // Parse args, do work, return JSON result
 *       return strdup("{\"result\": 42}");
 *   }
 *   
 *   NEXUS_EXPORT(my_function, "int,int", "int");
 */
#define NEXUS_EXPORT(fn, param_types, return_type) \
    __attribute__((constructor, unused)) static void __nexus_register_##fn(void) { \
        nexus_register_function(#fn, fn, param_types, return_type); \
    }

/**
 * NEXUS_EXPORT_NAMED - Register with a custom name.
 * 
 * Usage:
 *   NEXUS_EXPORT_NAMED("custom_name", my_function, "int", "int");
 */
#define NEXUS_EXPORT_NAMED(name, fn, param_types, return_type) \
    __attribute__((constructor, unused)) static void __nexus_register_##fn(void) { \
        nexus_register_function(name, fn, param_types, return_type); \
    }

/* ============================================================================
 * Registration Functions
 * ============================================================================ */

/**
 * Initialize the process ID.
 */
__attribute__((unused)) static void nexus_init_process_id(void) {
    if (nexus_process_id[0] == '\0') {
        /* Generate simple process ID from time and PID */
        srand((unsigned int)time(NULL) ^ (unsigned int)getpid());
        snprintf(nexus_process_id, sizeof(nexus_process_id), 
                 "%08x", rand());
    }
}

/**
 * Register a function for cross-language calling.
 */
__attribute__((unused)) static int nexus_register_function(
    const char* name,
    NexusExportedFunction handler,
    const char* param_types,
    const char* return_type
) {
    if (nexus_function_count >= MAX_EXPORTED_FUNCTIONS) {
        fprintf(stderr, "[NEXUS-C] ERROR: Too many exported functions\n");
        return -1;
    }
    
    nexus_init_process_id();
    
    NexusFunctionEntry* entry = &nexus_functions[nexus_function_count++];
    strncpy(entry->name, name, MAX_FUNCTION_NAME_LEN - 1);
    entry->handler = handler;
    strncpy(entry->param_types, param_types, sizeof(entry->param_types) - 1);
    strncpy(entry->return_type, return_type, sizeof(entry->return_type) - 1);
    entry->registered = 1;
    
    printf("[NEXUS-C] Registered function: %s\n", name);
    return 0;
}

/**
 * Find a registered function by name.
 */
__attribute__((unused)) static NexusFunctionEntry* nexus_find_function(const char* name) {
    for (int i = 0; i < nexus_function_count; i++) {
        if (nexus_functions[i].registered && 
            strcmp(nexus_functions[i].name, name) == 0) {
            return &nexus_functions[i];
        }
    }
    return NULL;
}

/* ============================================================================
 * Call Handling
 * ============================================================================ */

/**
 * Publish function registry to Redis.
 * Called after all functions are registered.
 */
__attribute__((unused)) static int nexus_publish_registry(void) {
    if (g_nexus == NULL) {
        if (nexus_init() != NEXUS_OK) {
            return -1;
        }
    }
    
    /* Build registry JSON */
    char registry_json[4096];
    int offset = 0;
    
    offset += snprintf(registry_json + offset, sizeof(registry_json) - offset, "{");
    
    for (int i = 0; i < nexus_function_count; i++) {
        NexusFunctionEntry* fn = &nexus_functions[i];
        if (!fn->registered) continue;
        
        if (i > 0) {
            offset += snprintf(registry_json + offset, sizeof(registry_json) - offset, ",");
        }
        
        offset += snprintf(registry_json + offset, sizeof(registry_json) - offset,
            "\"%s\":{\"name\":\"%s\",\"lang\":\"c\",\"pid\":\"%s\",\"params\":\"%s\",\"ret\":\"%s\"}",
            fn->name, fn->name, nexus_process_id, fn->param_types, fn->return_type);
    }
    
    snprintf(registry_json + offset, sizeof(registry_json) - offset, "}");
    
    /* Publish registry via Redis */
    return nexus_publish_event("registry_publish", registry_json);
}

/**
 * Process incoming function calls from Redis pub/sub.
 * This should be called when a function_call event is received.
 * Returns number of calls processed, or -1 on error.
 */
__attribute__((unused)) static int nexus_process_call(const char* call_json) {
    /* Parse call JSON - simplified implementation */
    /* In production, use a proper JSON parser like cJSON or jansson */
    
    /* Extract function name */
    char fn_name[MAX_FUNCTION_NAME_LEN] = {0};
    const char* fn_key = "\"fn\":\"";
    const char* fn_start = strstr(call_json, fn_key);
    if (fn_start) {
        fn_start += strlen(fn_key);
        const char* fn_end = strchr(fn_start, '"');
        if (fn_end) {
            size_t len = fn_end - fn_start;
            if (len < MAX_FUNCTION_NAME_LEN) {
                strncpy(fn_name, fn_start, len);
            }
        }
    }
    
    /* Find and call the function */
    NexusFunctionEntry* fn = nexus_find_function(fn_name);
    if (fn && fn->handler) {
        char* result = fn->handler(call_json);
        if (result) {
            /* Publish result via Redis */
            char result_msg[1024];
            snprintf(result_msg, sizeof(result_msg),
                     "{\"type\":\"function_result\",\"fn\":\"%s\",\"result\":%s}",
                     fn_name, result);
            nexus_publish_event("function_result", result_msg);
            free(result);
            return 1;
        }
    }
    
    return 0;
}

/**
 * Run the call handler loop (blocking).
 * Use this in main() after registering functions.
 * This subscribes to Redis and processes incoming function calls.
 */
__attribute__((unused)) static void nexus_run_handler(void) {
    printf("[NEXUS-C] Starting call handler loop...\n");
    
    /* Initialize Nexus */
    if (nexus_init() != NEXUS_OK) {
        fprintf(stderr, "[NEXUS-C] Failed to initialize Nexus\n");
        return;
    }
    
    /* Publish registry first */
    if (nexus_publish_registry() != 0) {
        fprintf(stderr, "[NEXUS-C] Failed to publish registry\n");
        return;
    }
    
    /* Subscribe to Redis channels */
    if (nexus_subscribe() != NEXUS_OK) {
        fprintf(stderr, "[NEXUS-C] Failed to subscribe to Redis\n");
        return;
    }
    
    /* Set up event handler for function calls */
    nexus_on_event([](const char* channel, const char* message) {
        if (strcmp(channel, CHANNEL_EVENTS) == 0) {
            /* Check if this is a function call */
            if (strstr(message, "\"type\":\"function_call\"")) {
                nexus_process_call(message);
            }
        }
    });
    
    /* Process messages in a loop */
    nexus_process_messages();
}

/* ============================================================================
 * JSON Helpers (minimal implementation)
 * ============================================================================ */

/**
 * Extract a string value from JSON by key.
 * Returns malloc'd string, caller must free.
 */
__attribute__((unused)) static char* json_get_string(const char* json, const char* key) {
    char search[128];
    snprintf(search, sizeof(search), "\"%s\":\"", key);
    
    char* start = strstr(json, search);
    if (!start) return NULL;
    
    start += strlen(search);
    char* end = strchr(start, '"');
    if (!end) return NULL;
    
    size_t len = end - start;
    char* result = (char*)malloc(len + 1);
    strncpy(result, start, len);
    result[len] = '\0';
    
    return result;
}

/**
 * Create a JSON result string.
 */
__attribute__((unused)) static char* json_result(const char* value) {
    size_t len = strlen(value) + 32;
    char* result = (char*)malloc(len);
    snprintf(result, len, "{\"result\":%s}", value);
    return result;
}

/**
 * Create a JSON error string.
 */
__attribute__((unused)) static char* json_error(const char* message) {
    size_t len = strlen(message) + 32;
    char* result = (char*)malloc(len);
    snprintf(result, len, "{\"error\":\"%s\"}", message);
    return result;
}

#endif /* NEXUS_EXPORT_H */
