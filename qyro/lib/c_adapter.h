/*
 * Qyro C Adapter v1 - Cross-Language RPC Support
 *
 * Provides the Qyro API for C services:
 * - Shared state (Redis via hiredis)
 * - Event streaming (Kafka via librdkafka)
 * - Cross-language RPC
 *
 * For detailed usage examples, visit: https://qyro.dev/docs/c-adapter
 */

#ifndef QYRO_ADAPTER_H
#define QYRO_ADAPTER_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <hiredis/hiredis.h>
#include <librdkafka/rdkafka.h>
#include <cJSON/cJSON.h>
#include <pthread.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Configuration */
#define QYRO_RPC_TOPIC "qyro.rpc.requests"
#define QYRO_RPC_RESP_TOPIC "qyro.rpc.responses"
#define QYRO_MAX_FUNCS 100
#define QYRO_RPC_TIMEOUT 30

/* Get environment variable with fallback */
static inline const char* qyro_getenv(const char* key, const char* fallback) {
    const char* val = getenv(key);
    return val ? val : fallback;
}

/* Global configuration */
static const char* QYRO_REDIS_HOST;
static int QYRO_REDIS_PORT;
static const char* QYRO_KAFKA_SERVERS;
static const char* QYRO_SERVICE_NAME;

/* Redis connection */
static redisContext* _redis_ctx = NULL;

/* Function registry */
typedef char* (*QyroRPCHandler)(cJSON* args);

typedef struct {
    char name[256];
    QyroRPCHandler handler;
} QyroFunction;

static QyroFunction _exposed_funcs[QYRO_MAX_FUNCS];
static int _func_count = 0;
static pthread_mutex_t _func_mutex = PTHREAD_MUTEX_INITIALIZER;

/* ============================================================================
 * Initialization
 * =========================================================================== */

static void qyro_init(void) {
    QYRO_REDIS_HOST = qyro_getenv("REDIS_HOST", "redis");
    QYRO_REDIS_PORT = atoi(qyro_getenv("REDIS_PORT", "6379"));
    QYRO_KAFKA_SERVERS = qyro_getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092");
    QYRO_SERVICE_NAME = qyro_getenv("QYRO_SERVICE_NAME", "c-service");
}

/* ============================================================================
 * Logging
 * =========================================================================== */

static void qyro_log(const char* level, const char* message) {
    time_t now = time(NULL);
    char ts[64];
    strftime(ts, sizeof(ts), "%Y-%m-%dT%H:%M:%S", localtime(&now));
    printf("[%s] [%s] [%s] %s\n", ts, level, QYRO_SERVICE_NAME, message);
    fflush(stdout);
}

#define qyro_info(msg) qyro_log("INFO", msg)
#define qyro_warn(msg) qyro_log("WARN", msg)
#define qyro_error(msg) qyro_log("ERROR", msg)
#define qyro_debug(msg) qyro_log("DEBUG", msg)

/* ============================================================================
 * Redis API
 * =========================================================================== */

static redisContext* qyro_get_redis(void) {
    if (!_redis_ctx) {
        _redis_ctx = redisConnect(QYRO_REDIS_HOST, QYRO_REDIS_PORT);
        if (_redis_ctx->err) {
            qyro_error("Redis connection failed");
            return NULL;
        }
    }
    return _redis_ctx;
}

static int qyro_set(const char* key, const char* value) {
    redisContext* ctx = qyro_get_redis();
    if (!ctx) return -1;
    
    redisReply* reply = redisCommand(ctx, "SET %s %s", key, value);
    if (!reply) return -1;
    
    freeReplyObject(reply);
    return 0;
}

static char* qyro_get(const char* key) {
    redisContext* ctx = qyro_get_redis();
    if (!ctx) return NULL;

    redisReply* reply = redisCommand(ctx, "GET %s", key);
    if (!reply || reply->type != REDIS_REPLY_STRING) {
        if (reply) freeReplyObject(reply);
        return NULL;
    }

    char* result = NULL;
    if (reply->str) {
        result = strdup(reply->str);
    }
    freeReplyObject(reply);
    return result;
}

static int qyro_del(const char* key) {
    redisContext* ctx = qyro_get_redis();
    if (!ctx) return -1;
    
    redisReply* reply = redisCommand(ctx, "DEL %s", key);
    if (!reply) return -1;
    
    int deleted = (reply->type == REDIS_REPLY_INTEGER) ? (int)reply->integer : 0;
    freeReplyObject(reply);
    return deleted;
}

static int qyro_exists(const char* key) {
    redisContext* ctx = qyro_get_redis();
    if (!ctx) return 0;
    
    redisReply* reply = redisCommand(ctx, "EXISTS %s", key);
    if (!reply) return 0;
    
    int exists = (reply->type == REDIS_REPLY_INTEGER) ? (int)reply->integer : 0;
    freeReplyObject(reply);
    return exists;
}

static long long qyro_incr(const char* key, long long amount) {
    redisContext* ctx = qyro_get_redis();
    if (!ctx) return 0;
    
    redisReply* reply = redisCommand(ctx, "INCRBY %s %lld", key, amount);
    if (!reply) return 0;
    
    long long result = (reply->type == REDIS_REPLY_INTEGER) ? reply->integer : 0;
    freeReplyObject(reply);
    return result;
}

/* ============================================================================
 * Kafka API
 * =========================================================================== */

static int qyro_publish(const char* topic, const char* message) {
    rd_kafka_t* producer;
    rd_kafka_conf_t* conf;
    char errstr[512];
    
    conf = rd_kafka_conf_new();
    if (rd_kafka_conf_set(conf, "bootstrap.servers", QYRO_KAFKA_SERVERS,
                          errstr, sizeof(errstr)) != RD_KAFKA_CONF_OK) {
        qyro_error(errstr);
        return -1;
    }
    
    producer = rd_kafka_new(RD_KAFKA_PRODUCER, conf, errstr, sizeof(errstr));
    if (!producer) {
        qyro_error(errstr);
        return -1;
    }
    
    rd_kafka_producev(
        producer,
        RD_KAFKA_V_TOPIC(topic),
        RD_KAFKA_V_VALUE((void*)message, strlen(message)),
        RD_KAFKA_V_END
    );
    
    rd_kafka_flush(producer, 5000);
    rd_kafka_destroy(producer);
    
    return 0;
}

/* ============================================================================
 * RPC API
 * =========================================================================== */

static void qyro_expose(const char* name, QyroRPCHandler handler) {
    pthread_mutex_lock(&_func_mutex);
    
    if (_func_count < QYRO_MAX_FUNCS) {
        snprintf(_exposed_funcs[_func_count].name, 256, "%s.%s", 
                 QYRO_SERVICE_NAME, name);
        _exposed_funcs[_func_count].handler = handler;
        _func_count++;
        
        char msg[512];
        snprintf(msg, sizeof(msg), "Exposed function: %s.%s", QYRO_SERVICE_NAME, name);
        qyro_info(msg);
    }
    
    pthread_mutex_unlock(&_func_mutex);
}

static QyroRPCHandler qyro_find_function(const char* name) {
    pthread_mutex_lock(&_func_mutex);
    
    for (int i = 0; i < _func_count; i++) {
        if (strcmp(_exposed_funcs[i].name, name) == 0) {
            pthread_mutex_unlock(&_func_mutex);
            return _exposed_funcs[i].handler;
        }
    }
    
    pthread_mutex_unlock(&_func_mutex);
    return NULL;
}

/* Generate UUID (simplified) */
static void qyro_uuid(char* buf) {
    sprintf(buf, "%08x-%04x-%04x-%04x-%012x",
            rand(), rand() & 0xFFFF, rand() & 0xFFFF,
            rand() & 0xFFFF, rand());
}

static char* qyro_call(const char* function_path, cJSON* args) {
    char request_id[64];
    qyro_uuid(request_id);

    /* Extract target service */
    char target[128] = {0};
    const char* dot = strchr(function_path, '.');
    if (dot) {
        strncpy(target, function_path, dot - function_path);
        target[dot - function_path] = '\0';
    } else {
        strcpy(target, function_path);
    }

    /* Build request JSON */
    cJSON* request = cJSON_CreateObject();
    cJSON_AddStringToObject(request, "request_id", request_id);
    cJSON_AddStringToObject(request, "source_service", QYRO_SERVICE_NAME);
    cJSON_AddStringToObject(request, "target_service", target);
    cJSON_AddStringToObject(request, "function_name", function_path);
    cJSON_AddItemToObject(request, "args", args ? cJSON_Duplicate(args, 1) : cJSON_CreateArray());
    cJSON_AddObjectToObject(request, "kwargs");
    cJSON_AddNumberToObject(request, "timestamp", (double)time(NULL));

    char* req_str = cJSON_PrintUnformatted(request);

    // Create a temporary entry for the pending request
    // In a real implementation, we'd use a proper synchronization mechanism
    // For now, we'll return a placeholder that indicates this is not fully implemented
    // since synchronous calls in C require complex thread synchronization

    char* result = strdup("{\"error\": \"Synchronous RPC calls not fully implemented in C adapter\"}");

    free(req_str);
    cJSON_Delete(request);

    return result;
}

/* RPC Server thread function */
static void* qyro_rpc_server_thread(void* arg) {
    rd_kafka_t* consumer;
    rd_kafka_conf_t* conf;
    rd_kafka_topic_partition_list_t* topics;
    char errstr[512];

    conf = rd_kafka_conf_new();
    rd_kafka_conf_set(conf, "bootstrap.servers", QYRO_KAFKA_SERVERS, NULL, 0);

    char group_id[256];
    snprintf(group_id, sizeof(group_id), "qyro-rpc-server-%s", QYRO_SERVICE_NAME);
    rd_kafka_conf_set(conf, "group.id", group_id, NULL, 0);
    rd_kafka_conf_set(conf, "auto.offset.reset", "latest", NULL, 0);

    consumer = rd_kafka_new(RD_KAFKA_CONSUMER, conf, errstr, sizeof(errstr));
    if (!consumer) {
        qyro_error("Failed to create consumer");
        return NULL;
    }

    topics = rd_kafka_topic_partition_list_new(1);
    rd_kafka_topic_partition_list_add(topics, QYRO_RPC_TOPIC, RD_KAFKA_PARTITION_UA);
    rd_kafka_subscribe(consumer, topics);
    rd_kafka_topic_partition_list_destroy(topics);

    char msg[256];
    snprintf(msg, sizeof(msg), "RPC Server started for service: %s", QYRO_SERVICE_NAME);
    qyro_info(msg);

    // Set a timeout to allow checking for termination condition
    while (1) {
        rd_kafka_message_t* rkmsg = rd_kafka_consumer_poll(consumer, 1000); // 1 second timeout

        // Check for termination signal here if needed
        // For now, we'll just continue processing messages

        if (!rkmsg) continue;

        if (rkmsg->err) {
            // Handle specific errors appropriately
            if (rkmsg->err == RD_KAFKA_RESP_ERR__TIMED_OUT) {
                // This is expected with our timeout, continue to next iteration
                rd_kafka_message_destroy(rkmsg);
                continue;
            }

            rd_kafka_message_destroy(rkmsg);
            continue;
        }

        /* Parse request */
        cJSON* request = cJSON_ParseWithLength(rkmsg->payload, rkmsg->len);
        if (!request) {
            rd_kafka_message_destroy(rkmsg);
            continue;
        }

        cJSON* target = cJSON_GetObjectItem(request, "target_service");
        if (!target || strcmp(target->valuestring, QYRO_SERVICE_NAME) != 0) {
            cJSON_Delete(request);
            rd_kafka_message_destroy(rkmsg);
            continue;
        }

        /* Handle request */
        cJSON* func_name = cJSON_GetObjectItem(request, "function_name");
        cJSON* args = cJSON_GetObjectItem(request, "args");
        cJSON* req_id = cJSON_GetObjectItem(request, "request_id");

        QyroRPCHandler handler = qyro_find_function(func_name->valuestring);

        cJSON* response = cJSON_CreateObject();
        cJSON_AddStringToObject(response, "request_id", req_id->valuestring);
        cJSON_AddStringToObject(response, "source_service", QYRO_SERVICE_NAME);
        cJSON_AddNumberToObject(response, "timestamp", (double)time(NULL));

        if (handler) {
            char* result = handler(args);
            cJSON_AddBoolToObject(response, "success", 1);
            cJSON* res_json = cJSON_Parse(result);
            cJSON_AddItemToObject(response, "result", res_json ? res_json : cJSON_CreateString(result));
            free(result);
        } else {
            cJSON_AddBoolToObject(response, "success", 0);
            cJSON_AddNullToObject(response, "result");
            char err_msg[256];
            snprintf(err_msg, sizeof(err_msg), "Function '%s' not found", func_name->valuestring);
            cJSON_AddStringToObject(response, "error", err_msg);
        }

        char* resp_str = cJSON_PrintUnformatted(response);
        qyro_publish(QYRO_RPC_RESP_TOPIC, resp_str);

        free(resp_str);
        cJSON_Delete(response);
        cJSON_Delete(request);
        rd_kafka_message_destroy(rkmsg);
    }

    rd_kafka_destroy(consumer);
    return NULL;
}

static void qyro_start_rpc_server(void) {
    pthread_t thread;
    pthread_create(&thread, NULL, qyro_rpc_server_thread, NULL);
    pthread_detach(thread);
}

/* ============================================================================
 * Service Discovery
 * =========================================================================== */

static void qyro_register_service(void) {
    cJSON* info = cJSON_CreateObject();
    cJSON_AddStringToObject(info, "name", QYRO_SERVICE_NAME);
    cJSON_AddStringToObject(info, "host", qyro_getenv("HOSTNAME", "localhost"));
    
    char* info_str = cJSON_PrintUnformatted(info);
    char key[256];
    snprintf(key, sizeof(key), "qyro:service:%s", QYRO_SERVICE_NAME);
    qyro_set(key, info_str);
    
    char msg[256];
    snprintf(msg, sizeof(msg), "Service registered: %s", QYRO_SERVICE_NAME);
    qyro_info(msg);
    
    free(info_str);
    cJSON_Delete(info);
}

#ifdef __cplusplus
}
#endif

#endif /* QYRO_ADAPTER_H */
