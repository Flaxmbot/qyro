package com.qyro.adapters;

import redis.clients.jedis.Jedis;
import org.apache.kafka.clients.producer.*;
import org.apache.kafka.clients.consumer.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Properties;
import java.util.Collections;
import java.time.Duration;

public class Qyro {
    private static final String REDIS_HOST = System.getenv().getOrDefault("REDIS_HOST", "redis");
    private static final int REDIS_PORT = Integer.parseInt(System.getenv().getOrDefault("REDIS_PORT", "6379"));
    private static final String KAFKA_SERVERS = System.getenv().getOrDefault("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092");

    private static final ObjectMapper mapper = new ObjectMapper();

    public static void set(String key, Object value) {
        try (Jedis jedis = new Jedis(REDIS_HOST, REDIS_PORT)) {
            String val = mapper.writeValueAsString(value);
            jedis.set(key, val);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static String get(String key) {
        try (Jedis jedis = new Jedis(REDIS_HOST, REDIS_PORT)) {
            return jedis.get(key);
        }
    }

    public static void publish(String topic, Object message) {
        Properties props = new Properties();
        props.put("bootstrap.servers", KAFKA_SERVERS);
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        try (Producer<String, String> producer = new KafkaProducer<>(props)) {
            String val = mapper.writeValueAsString(message);
            producer.send(new ProducerRecord<>(topic, "key", val));
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
