import os
import json
import time
import threading
import logging
from typing import Any, Callable, Dict, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [QYRO] %(message)s')
logger = logging.getLogger("qyro.lib")

class QyroClient:
    def __init__(self):
        self._redis = None
        self._kafka_producer = None
        self._kafka_consumer = None
        self._handlers = {}
        self._running = False
        self._connect_redis()
        self._connect_kafka_producer()

    def _connect_redis(self):
        host = os.environ.get("QYRO_REDIS_HOST", "localhost")
        port = int(os.environ.get("QYRO_REDIS_PORT", 6379))
        password = os.environ.get("QYRO_REDIS_PASSWORD", None)

        try:
            import redis
            self._redis = redis.Redis(
                host=host,
                port=port,
                password=password,
                decode_responses=True
            )
            self._redis.ping()
        except ImportError:
            logger.warning("Redis library not installed. Shared state disabled.")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Shared state disabled.")
            self._redis = None

    def _connect_kafka_producer(self):
        bootstrap_servers = os.environ.get("QYRO_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

        try:
            from confluent_kafka import Producer
            self._kafka_producer = Producer({
                'bootstrap.servers': bootstrap_servers,
                'client.id': os.environ.get("QYRO_MODULE_NAME", "qyro-python-client")
            })
        except ImportError:
            logger.warning("confluent-kafka not installed. Messaging disabled.")
        except Exception as e:
            logger.warning(f"Failed to connect to Kafka: {e}. Messaging disabled.")
            self._kafka_producer = None

    def get(self, key: str) -> Any:
        """Get a value from shared state."""
        if not self._redis: return None
        val = self._redis.get(key)
        try:
            return json.loads(val) if val else None
        except (json.JSONDecodeError, TypeError):
            return val

    def set(self, key: str, value: Any):
        """Set a value in shared state."""
        if not self._redis: return
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        self._redis.set(key, value)

    def emit(self, topic: str, data: Any):
        """Emit an event to a topic."""
        if self._kafka_producer:
            # Use Kafka
            if isinstance(data, (dict, list)):
                data = json.dumps(data)
            elif not isinstance(data, str):
                data = str(data)

            self._kafka_producer.produce(topic, data.encode('utf-8'))
            self._kafka_producer.flush()
        elif self._redis:
            # Fallback to Redis Pub/Sub
            if isinstance(data, (dict, list)):
                data = json.dumps(data)
            self._redis.publish(f"qyro:{topic}", data)
        else:
            logger.warning("No message broker available. Event dropped.")

    def on(self, topic: str):
        """Decorator to register an event handler."""
        def decorator(func: Callable):
            self._handlers[topic] = func
            return func
        return decorator

    def start(self):
        """Start listening for events (blocking)."""
        self._running = True

        # Check if we should use Kafka or Redis for consumption
        kafka_servers = os.environ.get("QYRO_KAFKA_BOOTSTRAP_SERVERS")

        if kafka_servers and self._kafka_producer: # implied kafka availability
            self._start_kafka_consumer(kafka_servers)
        elif self._redis:
            self._start_redis_consumer()
        else:
            logger.error("No message broker available. Cannot start listener.")

    def _start_kafka_consumer(self, bootstrap_servers):
        from confluent_kafka import Consumer

        conf = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': os.environ.get("QYRO_MODULE_NAME", "qyro_group"),
            'auto.offset.reset': 'latest'
        }

        consumer = Consumer(conf)
        consumer.subscribe(list(self._handlers.keys()))

        logger.info(f"Listening for events on Kafka: {list(self._handlers.keys())}")

        try:
            while self._running:
                msg = consumer.poll(1.0)
                if msg is None: continue
                if msg.error():
                    logger.error(f"Consumer error: {msg.error()}")
                    continue

                topic = msg.topic()
                if topic in self._handlers:
                    data = msg.value().decode('utf-8')
                    try:
                        data = json.loads(data)
                    except: pass

                    try:
                        self._handlers[topic](data)
                    except Exception as e:
                        logger.error(f"Error in handler for {topic}: {e}")
        finally:
            consumer.close()

    def _start_redis_consumer(self):
        pubsub = self._redis.pubsub()
        # Subscribe to "qyro:topic" for each handler
        channels = {f"qyro:{t}": t for t in self._handlers.keys()}
        pubsub.subscribe(*channels.keys())

        logger.info(f"Listening for events on Redis: {list(self._handlers.keys())}")

        for message in pubsub.listen():
            if not self._running: break
            if message['type'] == 'message':
                channel = message['channel']
                topic = channels.get(channel)
                if topic and topic in self._handlers:
                    data = message['data']
                    try:
                        data = json.loads(data)
                    except: pass

                    try:
                        self._handlers[topic](data)
                    except Exception as e:
                        logger.error(f"Error in handler for {topic}: {e}")

# Create singleton instance
qyro = QyroClient()
get = qyro.get
set = qyro.set
emit = qyro.emit
on = qyro.on
start = qyro.start
