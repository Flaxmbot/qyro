// src/adapters/language_adapters/java/NexusAdapter.java
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.apache.kafka.clients.producer.*;
import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.serialization.StringSerializer;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.params.SetParams;

import java.util.*;
import java.util.concurrent.Future;
import java.util.concurrent.ExecutionException;
import java.time.Instant;

public class NexusAdapter {
    private String kafkaBootstrapServers;
    private String redisHost;
    private int redisPort;
    private String moduleName;
    private Properties kafkaProps;
    private Producer<String, String> kafkaProducer;
    private JedisPool jedisPool;
    private ObjectMapper objectMapper;
    private Map<String, Object> stateCache;

    public NexusAdapter(String moduleName) {
        this.moduleName = moduleName;
        this.kafkaBootstrapServers = "localhost:9092";
        this.redisHost = "localhost";
        this.redisPort = 6379;
        this.objectMapper = new ObjectMapper();
        this.stateCache = new HashMap<>();
        
        initializeKafka();
        initializeRedis();
        registerModule();
    }

    public NexusAdapter(String kafkaBootstrapServers, String redisHost, int redisPort, String moduleName) {
        this.moduleName = moduleName;
        this.kafkaBootstrapServers = kafkaBootstrapServers;
        this.redisHost = redisHost;
        this.redisPort = redisPort;
        this.objectMapper = new ObjectMapper();
        this.stateCache = new HashMap<>();
        
        initializeKafka();
        initializeRedis();
        registerModule();
    }

    private void initializeKafka() {
        kafkaProps = new Properties();
        kafkaProps.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, kafkaBootstrapServers);
        kafkaProps.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        kafkaProps.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        kafkaProps.put(ProducerConfig.ACKS_CONFIG, "1");
        
        this.kafkaProducer = new KafkaProducer<>(kafkaProps);
    }

    private void initializeRedis() {
        this.jedisPool = new JedisPool(redisHost, redisPort);
    }

    private void registerModule() {
        try {
            ObjectNode registration = objectMapper.createObjectNode();
            registration.put("type", "module_registration");
            registration.put("module_name", this.moduleName);
            registration.put("timestamp", Instant.now().toString());
            registration.put("language", "java");

            ProducerRecord<String, String> record = new ProducerRecord<>("nexus_module_events", 
                this.moduleName, objectMapper.writeValueAsString(registration));
            kafkaProducer.send(record);
        } catch (Exception e) {
            System.err.println("Error registering module: " + e.getMessage());
        }
    }

    public Map<String, Object> readState() {
        try (Jedis jedis = jedisPool.getResource()) {
            Map<String, String> redisState = jedis.hgetAll("nexus:state");
            Map<String, Object> state = new HashMap<>();

            for (Map.Entry<String, String> entry : redisState.entrySet()) {
                try {
                    JsonNode jsonNode = objectMapper.readTree(entry.getValue());
                    state.put(entry.getKey(), objectMapper.convertValue(jsonNode, Object.class));
                } catch (Exception e) {
                    // If JSON parsing fails, store as string
                    state.put(entry.getKey(), entry.getValue());
                }
            }

            this.stateCache = state;
            return state;
        }
    }

    public void writeState(Map<String, Object> state) {
        try (Jedis jedis = jedisPool.getResource()) {
            Map<String, String> redisState = new HashMap<>();
            
            for (Map.Entry<String, Object> entry : state.entrySet()) {
                try {
                    String valueStr = objectMapper.writeValueAsString(entry.getValue());
                    redisState.put(entry.getKey(), valueStr);
                } catch (Exception e) {
                    System.err.println("Error serializing value for key " + entry.getKey() + ": " + e.getMessage());
                }
            }
            
            jedis.hset("nexus:state", redisState);

            // Publish state change event to Kafka
            ObjectNode stateChange = objectMapper.createObjectNode();
            stateChange.put("type", "state_change");
            stateChange.put("module", this.moduleName);
            stateChange.set("changes", objectMapper.valueToTree(state));
            stateChange.put("timestamp", Instant.now().toString());

            ProducerRecord<String, String> record = new ProducerRecord<>("nexus_state_changes", 
                this.moduleName, objectMapper.writeValueAsString(stateChange));
            kafkaProducer.send(record);
        } catch (Exception e) {
            System.err.println("Error writing state: " + e.getMessage());
        }
    }

    public void updateField(String key, Object value) {
        try (Jedis jedis = jedisPool.getResource()) {
            String valueStr = objectMapper.writeValueAsString(value);
            jedis.hset("nexus:state", key, valueStr);

            // Publish field update event to Kafka
            ObjectNode fieldUpdate = objectMapper.createObjectNode();
            fieldUpdate.put("type", "field_update");
            fieldUpdate.put("module", this.moduleName);
            fieldUpdate.put("key", key);
            fieldUpdate.set("value", objectMapper.valueToTree(value));
            fieldUpdate.put("timestamp", Instant.now().toString());

            ProducerRecord<String, String> record = new ProducerRecord<>("nexus_field_updates", 
                key, objectMapper.writeValueAsString(fieldUpdate));
            kafkaProducer.send(record);
        } catch (Exception e) {
            System.err.println("Error updating field: " + e.getMessage());
        }
    }

    public Object getField(String key) {
        Map<String, Object> state = readState();
        return state.get(key);
    }

    public long incrementField(String key, long amount) {
        Object currentValue = getField(key);
        long currentNum = 0;
        
        if (currentValue instanceof Number) {
            currentNum = ((Number) currentValue).longValue();
        } else if (currentValue instanceof String) {
            try {
                currentNum = Long.parseLong((String) currentValue);
            } catch (NumberFormatException e) {
                currentNum = 0;
            }
        }
        
        long newValue = currentNum + amount;
        updateField(key, newValue);
        return newValue;
    }

    public Object callRemoteFunction(String funcName, Object args) {
        try {
            String requestId = UUID.randomUUID().toString();
            ObjectNode callRequest = objectMapper.createObjectNode();
            callRequest.put("type", "rpc_call");
            callRequest.put("request_id", requestId);
            callRequest.put("function", funcName);
            callRequest.set("args", objectMapper.valueToTree(args));
            callRequest.put("caller", this.moduleName);
            callRequest.put("timestamp", Instant.now().toString());

            ProducerRecord<String, String> record = new ProducerRecord<>("nexus_rpc_requests", 
                funcName, objectMapper.writeValueAsString(callRequest));
            kafkaProducer.send(record);

            // In a real implementation, we'd wait for the response
            return "response_pending";
        } catch (Exception e) {
            System.err.println("Error calling remote function: " + e.getMessage());
            return null;
        }
    }

    public void registerFunction(String funcName, FunctionHandler handler) {
        try {
            ObjectNode registration = objectMapper.createObjectNode();
            registration.put("type", "function_registration");
            registration.put("function", funcName);
            registration.put("module", this.moduleName);
            registration.put("timestamp", Instant.now().toString());

            ProducerRecord<String, String> record = new ProducerRecord<>("nexus_function_registry", 
                funcName, objectMapper.writeValueAsString(registration));
            kafkaProducer.send(record);
        } catch (Exception e) {
            System.err.println("Error registering function: " + e.getMessage());
        }
    }

    public void subscribeToChanges(StateChangeListener listener) {
        // This would typically create a Kafka consumer
        // For now, we'll just log
        System.out.println("Subscribing to state changes...");
    }

    public void close() {
        if (kafkaProducer != null) {
            kafkaProducer.close();
        }
        if (jedisPool != null) {
            jedisPool.close();
        }
    }

    // Functional interface for function handlers
    @FunctionalInterface
    public interface FunctionHandler {
        Object handle(Object args);
    }

    // Functional interface for state change listeners
    @FunctionalInterface
    public interface StateChangeListener {
        void onChange(Map<String, Object> newState);
    }
}