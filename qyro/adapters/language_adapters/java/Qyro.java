package com.qyro;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.clients.producer.*;
import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.common.serialization.StringSerializer;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;

import java.util.*;

public class Qyro {
    private static Qyro instance;
    private Producer<String, String> producer;
    private JedisPool jedisPool;
    private ObjectMapper mapper = new ObjectMapper();
    private String moduleName;

    private Qyro() {
        moduleName = System.getenv().getOrDefault("QYRO_MODULE_NAME", "java_module");
        initRedis();
        initKafka();
    }

    public static synchronized Qyro getInstance() {
        if (instance == null) {
            instance = new Qyro();
        }
        return instance;
    }

    private void initRedis() {
        String host = System.getenv().getOrDefault("QYRO_REDIS_HOST", "localhost");
        int port = Integer.parseInt(System.getenv().getOrDefault("QYRO_REDIS_PORT", "6379"));
        jedisPool = new JedisPool(host, port);
    }

    private void initKafka() {
        Properties props = new Properties();
        String bootstrap = System.getenv().getOrDefault("QYRO_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092");
        props.put("bootstrap.servers", bootstrap);
        props.put("key.serializer", StringSerializer.class.getName());
        props.put("value.serializer", StringSerializer.class.getName());

        try {
            producer = new KafkaProducer<>(props);
        } catch (Exception e) {
            System.err.println("[QYRO] Kafka init failed: " + e.getMessage());
        }
    }

    // Static API
    public static <T> T get(String key, Class<T> clazz) {
        return getInstance().getImpl(key, clazz);
    }

    public static void set(String key, Object value) {
        getInstance().setImpl(key, value);
    }

    public static void emit(String topic, Object data) {
        getInstance().emitImpl(topic, data);
    }

    // Implementation
    private <T> T getImpl(String key, Class<T> clazz) {
        try (Jedis jedis = jedisPool.getResource()) {
            String val = jedis.get(key);
            if (val == null) return null;
            return mapper.readValue(val, clazz);
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    private void setImpl(String key, Object value) {
        try (Jedis jedis = jedisPool.getResource()) {
            String val = mapper.writeValueAsString(value);
            jedis.set(key, val);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void emitImpl(String topic, Object data) {
        try {
            String val = mapper.writeValueAsString(data);
            if (producer != null) {
                producer.send(new ProducerRecord<>(topic, moduleName, val));
            } else {
                // Redis Fallback
                try (Jedis jedis = jedisPool.getResource()) {
                    jedis.publish("qyro:" + topic, val);
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
