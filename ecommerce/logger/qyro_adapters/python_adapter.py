import os
import json
import redis
from kafka import KafkaProducer, KafkaConsumer

# Configuration from environment variables (set by docker-compose)
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

class Qyro:
    _redis = None
    _producer = None

    @classmethod
    def get_redis(cls):
        if cls._redis is None:
            cls._redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        return cls._redis

    @classmethod
    def get_producer(cls):
        if cls._producer is None:
            cls._producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                                          value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        return cls._producer

    @staticmethod
    def set(key: str, value):
        """Set a value in shared memory (Redis)."""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        Qyro.get_redis().set(key, value)

    @staticmethod
    def get(key: str):
        """Get a value from shared memory (Redis)."""
        val = Qyro.get_redis().get(key)
        try:
            return json.loads(val)
        except (TypeError, json.JSONDecodeError):
            return val

    @staticmethod
    def publish(topic: str, message: dict):
        """Publish a message to a topic (Kafka)."""
        producer = Qyro.get_producer()
        producer.send(topic, message)
        producer.flush()

    @staticmethod
    def subscribe(topic: str, group_id: str = "default"):
        """Generator to consume messages from a topic (Kafka)."""
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id=group_id,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        for message in consumer:
            yield message.value

# Expose simple API
set = Qyro.set
get = Qyro.get
publish = Qyro.publish
subscribe = Qyro.subscribe
