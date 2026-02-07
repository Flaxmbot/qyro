package com.qyro.adapters;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.JedisPoolConfig;
import org.apache.kafka.clients.producer.*;
import org.apache.kafka.clients.consumer.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;

import java.util.*;
import java.util.concurrent.*;
import java.util.function.Function;
import java.time.Duration;
import java.lang.annotation.*;

/**
 * Qyro Java Adapter v2 - Enhanced with RPC Support
 *
 * Provides the Qyro API for Java services:
 * - Shared state (Redis)
 * - Event streaming (Kafka)
 * - Cross-language RPC
 *
 * For detailed usage examples, visit: https://qyro.dev/docs/java-adapter
 */
public class Qyro {
    // Configuration
    private static final String REDIS_HOST = System.getenv().getOrDefault("REDIS_HOST", "redis");
    private static final int REDIS_PORT = Integer.parseInt(System.getenv().getOrDefault("REDIS_PORT", "6379"));
    private static final String KAFKA_SERVERS = System.getenv().getOrDefault("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092");
    private static final String SERVICE_NAME = System.getenv().getOrDefault("QYRO_SERVICE_NAME", "java-service");
    private static final String RPC_TOPIC = "qyro.rpc.requests";
    private static final String RPC_RESPONSE_TOPIC = "qyro.rpc.responses";
    private static final int RPC_TIMEOUT = Integer.parseInt(System.getenv().getOrDefault("QYRO_RPC_TIMEOUT", "30000"));

    private static final ObjectMapper mapper = new ObjectMapper();
    
    // Connection pools
    private static JedisPool jedisPool;
    private static Producer<String, String> kafkaProducer;
    
    // RPC State
    private static final Map<String, ExposedFunction> exposedFunctions = new ConcurrentHashMap<>();
    private static final Map<String, CompletableFuture<Object>> pendingRequests = new ConcurrentHashMap<>();
    private static volatile boolean rpcServerRunning = false;
    private static ExecutorService rpcExecutor;

    // ==========================================================================
    // Annotations
    // ==========================================================================

    /**
     * Annotation to expose a method for cross-language RPC calls.
     * 
     * @example
     * @Expose("calculate")
     * public static int calculate(int a, int b) {
     *     return a + b;
     * }
     */
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    public @interface Expose {
        String value() default "";
    }

    // ==========================================================================
    // Connection Management
    // ==========================================================================

    private static synchronized JedisPool getJedisPool() {
        if (jedisPool == null) {
            JedisPoolConfig config = new JedisPoolConfig();
            config.setMaxTotal(10);
            config.setMaxIdle(5);
            jedisPool = new JedisPool(config, REDIS_HOST, REDIS_PORT);
        }
        return jedisPool;
    }

    private static synchronized Producer<String, String> getProducer() {
        if (kafkaProducer == null) {
            Properties props = new Properties();
            props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, KAFKA_SERVERS);
            props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, 
                "org.apache.kafka.common.serialization.StringSerializer");
            props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, 
                "org.apache.kafka.common.serialization.StringSerializer");
            props.put(ProducerConfig.ACKS_CONFIG, "all");
            kafkaProducer = new KafkaProducer<>(props);
        }
        return kafkaProducer;
    }

    // ==========================================================================
    // Shared State API (Redis)
    // ==========================================================================

    /**
     * Set a value in shared memory (Redis).
     */
    public static void set(String key, Object value) {
        try (Jedis jedis = getJedisPool().getResource()) {
            String val = mapper.writeValueAsString(value);
            jedis.set(key, val);
        } catch (Exception e) {
            error("Failed to set key: " + key, e);
        }
    }

    /**
     * Get a value from shared memory (Redis).
     */
    public static String get(String key) {
        try (Jedis jedis = getJedisPool().getResource()) {
            return jedis.get(key);
        }
    }

    /**
     * Get a value and parse it as a specific type.
     */
    public static <T> T get(String key, Class<T> type) {
        try (Jedis jedis = getJedisPool().getResource()) {
            String val = jedis.get(key);
            if (val == null) return null;
            return mapper.readValue(val, type);
        } catch (Exception e) {
            error("Failed to get key: " + key, e);
            return null;
        }
    }

    /**
     * Delete a key from shared memory.
     */
    public static boolean delete(String key) {
        try (Jedis jedis = getJedisPool().getResource()) {
            return jedis.del(key) > 0;
        }
    }

    /**
     * Check if a key exists.
     */
    public static boolean exists(String key) {
        try (Jedis jedis = getJedisPool().getResource()) {
            return jedis.exists(key);
        }
    }

    /**
     * Increment a counter.
     */
    public static long incr(String key, long amount) {
        try (Jedis jedis = getJedisPool().getResource()) {
            return jedis.incrBy(key, amount);
        }
    }

    /**
     * Set expiration on a key.
     */
    public static boolean expire(String key, int seconds) {
        try (Jedis jedis = getJedisPool().getResource()) {
            return jedis.expire(key, seconds) == 1;
        }
    }

    // ==========================================================================
    // Event Streaming API (Kafka)
    // ==========================================================================

    /**
     * Publish a message to a topic.
     */
    public static void publish(String topic, Object message) {
        try {
            String val = mapper.writeValueAsString(message);
            getProducer().send(new ProducerRecord<>(topic, "key", val)).get();
        } catch (Exception e) {
            error("Failed to publish message", e);
        }
    }

    /**
     * Subscribe to a topic with a callback.
     */
    public static void subscribe(String topic, String groupId, 
            java.util.function.Consumer<JsonNode> callback) {
        
        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, KAFKA_SERVERS);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, groupId != null ? groupId : "qyro-" + SERVICE_NAME);
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, 
            "org.apache.kafka.common.serialization.StringDeserializer");
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, 
            "org.apache.kafka.common.serialization.StringDeserializer");
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");

        Consumer<String, String> consumer = new KafkaConsumer<>(props);
        consumer.subscribe(Collections.singletonList(topic));

        new Thread(() -> {
            while (true) {
                try {
                    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(1000));
                    for (ConsumerRecord<String, String> record : records) {
                        JsonNode value = mapper.readTree(record.value());
                        callback.accept(value);
                    }
                } catch (Exception e) {
                    error("Error in consumer loop", e);
                }
            }
        }, "qyro-subscriber-" + topic).start();
    }

    // ==========================================================================
    // Cross-Language RPC API
    // ==========================================================================

    /**
     * Container for exposed function information.
     */
    private static class ExposedFunction {
        String name;
        String fullName;
        Function<Object[], Object> fn;
        
        ExposedFunction(String name, Function<Object[], Object> fn) {
            this.name = name;
            this.fullName = SERVICE_NAME + "." + name;
            this.fn = fn;
        }
    }

    /**
     * Register a function for RPC calls.
     */
    public static void expose(String name, Function<Object[], Object> fn) {
        String fullName = SERVICE_NAME + "." + name;
        exposedFunctions.put(fullName, new ExposedFunction(name, fn));
        info("Exposed function: " + fullName);
    }

    /**
     * Call a function in another service.
     * 
     * @param functionPath Full path like "service-name.function_name"
     * @param args Arguments to pass
     * @return The result of the remote function call
     */
    public static Object call(String functionPath, Object... args) {
        return call(functionPath, RPC_TIMEOUT, args);
    }

    /**
     * Call a function with custom timeout.
     */
    public static Object call(String functionPath, int timeoutMs, Object... args) {
        try {
            String requestId = UUID.randomUUID().toString();
            String[] parts = functionPath.split("\\.", 2);
            String targetService = parts[0];

            Map<String, Object> request = new HashMap<>();
            request.put("request_id", requestId);
            request.put("source_service", SERVICE_NAME);
            request.put("target_service", targetService);
            request.put("function_name", functionPath);
            request.put("args", Arrays.asList(args));
            request.put("kwargs", Collections.emptyMap());
            request.put("timestamp", System.currentTimeMillis() / 1000.0);

            // Ensure response listener is running
            ensureResponseListener();

            // Create future for response
            CompletableFuture<Object> future = new CompletableFuture<>();
            pendingRequests.put(requestId, future);

            // Send request
            String requestJson = mapper.writeValueAsString(request);
            getProducer().send(new ProducerRecord<>(RPC_TOPIC, "key", requestJson)).get();

            // Wait for response
            return future.get(timeoutMs, TimeUnit.MILLISECONDS);

        } catch (TimeoutException e) {
            throw new RuntimeException("RPC call to '" + functionPath + "' timed out");
        } catch (Exception e) {
            throw new RuntimeException("RPC call failed: " + e.getMessage(), e);
        }
    }

    /**
     * Call a function asynchronously.
     */
    public static CompletableFuture<Object> callAsync(String functionPath, Object... args) {
        return CompletableFuture.supplyAsync(() -> call(functionPath, args));
    }

    /**
     * Start the RPC server to handle incoming calls.
     */
    public static synchronized void startRPCServer() {
        if (rpcServerRunning) return;
        rpcServerRunning = true;

        rpcExecutor = Executors.newFixedThreadPool(4);

        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, KAFKA_SERVERS);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, "qyro-rpc-server-" + SERVICE_NAME);
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, 
            "org.apache.kafka.common.serialization.StringDeserializer");
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, 
            "org.apache.kafka.common.serialization.StringDeserializer");
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "latest");

        Consumer<String, String> consumer = new KafkaConsumer<>(props);
        consumer.subscribe(Collections.singletonList(RPC_TOPIC));

        new Thread(() -> {
            while (rpcServerRunning) {
                try {
                    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(1000));
                    for (ConsumerRecord<String, String> record : records) {
                        rpcExecutor.submit(() -> handleRPCRequest(record.value()));
                    }
                } catch (Exception e) {
                    if (rpcServerRunning) {
                        error("Error in RPC server loop", e);
                    }
                }
            }
        }, "qyro-rpc-server").start();

        info("RPC Server started for service: " + SERVICE_NAME);
    }

    private static void handleRPCRequest(String message) {
        try {
            JsonNode request = mapper.readTree(message);
            String targetService = request.get("target_service").asText();

            // Check if this request is for us
            if (!targetService.equals(SERVICE_NAME)) return;

            String requestId = request.get("request_id").asText();
            String functionName = request.get("function_name").asText();
            
            Map<String, Object> response = new HashMap<>();
            response.put("request_id", requestId);
            response.put("source_service", SERVICE_NAME);
            response.put("timestamp", System.currentTimeMillis() / 1000.0);

            try {
                ExposedFunction func = exposedFunctions.get(functionName);
                if (func == null) {
                    throw new Exception("Function '" + functionName + "' not found");
                }

                // Parse args
                JsonNode argsNode = request.get("args");
                Object[] args = new Object[argsNode.size()];
                for (int i = 0; i < argsNode.size(); i++) {
                    args[i] = parseJsonValue(argsNode.get(i));
                }

                Object result = func.fn.apply(args);

                response.put("success", true);
                response.put("result", result);
                response.put("error", null);

            } catch (Exception e) {
                response.put("success", false);
                response.put("result", null);
                response.put("error", e.getMessage());
            }

            // Send response
            String responseJson = mapper.writeValueAsString(response);
            getProducer().send(new ProducerRecord<>(RPC_RESPONSE_TOPIC, "key", responseJson)).get();

        } catch (Exception e) {
            error("Error handling RPC request", e);
        }
    }

    private static Object parseJsonValue(JsonNode node) {
        if (node.isInt()) return node.asInt();
        if (node.isLong()) return node.asLong();
        if (node.isDouble()) return node.asDouble();
        if (node.isBoolean()) return node.asBoolean();
        if (node.isTextual()) return node.asText();
        if (node.isArray()) {
            List<Object> list = new ArrayList<>();
            for (JsonNode item : node) {
                list.add(parseJsonValue(item));
            }
            return list;
        }
        if (node.isObject()) {
            Map<String, Object> map = new HashMap<>();
            node.fields().forEachRemaining(entry -> {
                map.put(entry.getKey(), parseJsonValue(entry.getValue()));
            });
            return map;
        }
        return null;
    }

    private static volatile boolean responseListenerRunning = false;

    private static synchronized void ensureResponseListener() {
        if (responseListenerRunning) return;
        responseListenerRunning = true;

        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, KAFKA_SERVERS);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, 
            "qyro-rpc-client-" + SERVICE_NAME + "-" + UUID.randomUUID().toString().substring(0, 8));
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, 
            "org.apache.kafka.common.serialization.StringDeserializer");
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, 
            "org.apache.kafka.common.serialization.StringDeserializer");
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "latest");

        Consumer<String, String> consumer = new KafkaConsumer<>(props);
        consumer.subscribe(Collections.singletonList(RPC_RESPONSE_TOPIC));

        new Thread(() -> {
            while (true) {
                try {
                    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(1000));
                    for (ConsumerRecord<String, String> record : records) {
                        JsonNode response = mapper.readTree(record.value());
                        String requestId = response.get("request_id").asText();

                        CompletableFuture<Object> future = pendingRequests.remove(requestId);
                        if (future == null) continue;

                        boolean success = response.get("success").asBoolean();
                        if (success) {
                            future.complete(parseJsonValue(response.get("result")));
                        } else {
                            future.completeExceptionally(
                                new RuntimeException("RPC Error: " + response.get("error").asText())
                            );
                        }
                    }
                } catch (Exception e) {
                    error("Error in response listener", e);
                }
            }
        }, "qyro-response-listener").start();
    }

    /**
     * List all exposed functions.
     */
    public static List<Map<String, Object>> listExposedFunctions() {
        List<Map<String, Object>> functions = new ArrayList<>();
        for (ExposedFunction f : exposedFunctions.values()) {
            Map<String, Object> meta = new HashMap<>();
            meta.put("name", f.name);
            meta.put("fullName", f.fullName);
            meta.put("service", SERVICE_NAME);
            functions.add(meta);
        }
        return functions;
    }

    // ==========================================================================
    // Service Discovery
    // ==========================================================================

    /**
     * Register this service for discovery.
     */
    public static void registerService(Map<String, Object> metadata) {
        Map<String, Object> serviceInfo = new HashMap<>();
        serviceInfo.put("name", SERVICE_NAME);
        serviceInfo.put("host", System.getenv().getOrDefault("HOSTNAME", "localhost"));
        serviceInfo.put("functions", listExposedFunctions());
        if (metadata != null) {
            serviceInfo.putAll(metadata);
        }
        set("qyro:service:" + SERVICE_NAME, serviceInfo);
        info("Service registered: " + SERVICE_NAME);
    }

    // ==========================================================================
    // Logging
    // ==========================================================================

    public static void log(String message, String level) {
        String timestamp = java.time.Instant.now().toString();
        System.out.println("[" + timestamp + "] [" + level + "] [" + SERVICE_NAME + "] " + message);
        System.out.flush();
    }

    public static void info(String message) { log(message, "INFO"); }
    public static void warn(String message) { log(message, "WARN"); }
    public static void error(String message) { log(message, "ERROR"); }
    public static void error(String message, Throwable t) { 
        log(message + ": " + t.getMessage(), "ERROR"); 
    }
    public static void debug(String message) { log(message, "DEBUG"); }

    // ==========================================================================
    // Cleanup
    // ==========================================================================

    public static void shutdown() {
        rpcServerRunning = false;
        if (jedisPool != null) jedisPool.close();
        if (kafkaProducer != null) kafkaProducer.close();
        if (rpcExecutor != null) rpcExecutor.shutdown();
    }

    static {
        Runtime.getRuntime().addShutdownHook(new Thread(Qyro::shutdown));
    }
}
