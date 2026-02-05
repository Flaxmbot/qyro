"""
Kafka Manager for Nexus
Handles Kafka integration for inter-module communication.
"""

import asyncio
import json
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import logging

from .config import QyroConfig
from .logging import get_logger


logger = get_logger("nexus.kafka_manager")


@dataclass
class KafkaConfig:
    """Configuration for Kafka integration."""
    bootstrap_servers: str = "kafka:29092"
    topic_prefix: str = "nexus_"
    consumer_group: str = "nexus_group"
    enable_auto_commit: bool = True
    auto_offset_reset: str = "earliest"


class KafkaManager:
    """Manages Kafka producers and consumers for Nexus modules."""
    
    def __init__(self, config: QyroConfig):
        self.config = config
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        
        # Initialize Kafka configuration
        self.kafka_config = KafkaConfig(
            bootstrap_servers=config.kafka_bootstrap_servers
        )
        
        logger.info(f"Kafka manager initialized with servers: {self.kafka_config.bootstrap_servers}")

    async def start_producer(self):
        """Start the Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_config.bootstrap_servers.split(','),
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                acks='all'
            )
            await self.producer.start()
            logger.info("Kafka producer started successfully")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise

    async def start_consumer(self, topics: list):
        """Start the Kafka consumer."""
        try:
            self.consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=self.kafka_config.bootstrap_servers.split(','),
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                group_id=self.kafka_config.consumer_group,
                enable_auto_commit=self.kafka_config.enable_auto_commit,
                auto_offset_reset=self.kafka_config.auto_offset_reset
            )
            await self.consumer.start()
            logger.info(f"Kafka consumer started successfully for topics: {topics}")
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise

    async def stop_producer(self):
        """Stop the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def stop_consumer(self):
        """Stop the Kafka consumer."""
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")

    async def send_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None):
        """Send a message to a Kafka topic."""
        if not self.producer:
            await self.start_producer()
            
        try:
            await self.producer.send_and_wait(topic, message, key=key.encode('utf-8') if key else None)
            logger.debug(f"Message sent to topic '{topic}': {message}")
        except Exception as e:
            logger.error(f"Failed to send message to topic '{topic}': {e}")
            raise

    async def consume_messages(self, topic: str, callback: Callable[[Dict[str, Any]], None]):
        """Consume messages from a Kafka topic."""
        if not self.consumer:
            await self.start_consumer([topic])
            
        try:
            async for msg in self.consumer:
                if msg.topic == topic:
                    logger.debug(f"Received message from topic '{topic}': {msg.value}")
                    callback(msg.value)
        except Exception as e:
            logger.error(f"Error consuming messages from topic '{topic}': {e}")
            raise

    def start(self):
        """Initialize the Kafka manager. Async start must be called separately."""
        self.running = True
        logger.info("Kafka manager initialized (call start_async() to start producer)")

    async def start_async(self):
        """Start the Kafka manager in a background task."""
        self.running = True
        # Start producer in background
        await self.start_producer()
        logger.info("Kafka producer started")

    def stop(self):
        """Stop the Kafka manager."""
        self.running = False

    async def _run_producer(self):
        """Internal method to run the producer."""
        await self.start_producer()
        while self.running:
            await asyncio.sleep(0.1)  # Keep the task alive

    async def publish_state_change(self, state_diff: Dict[str, Any], module_name: str):
        """Publish a state change to the state change topic."""
        topic = f"{self.kafka_config.topic_prefix}state_change"
        message = {
            "module": module_name,
            "timestamp": asyncio.get_event_loop().time(),
            "state_diff": state_diff
        }
        await self.send_message(topic, message)

    async def subscribe_to_state_changes(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to state change events."""
        topic = f"{self.kafka_config.topic_prefix}state_change"
        await self.consume_messages(topic, callback)

    async def publish_module_event(self, event_type: str, module_name: str, data: Dict[str, Any]):
        """Publish a module event to the events topic."""
        topic = f"{self.kafka_config.topic_prefix}module_events"
        message = {
            "event_type": event_type,
            "module": module_name,
            "timestamp": asyncio.get_event_loop().time(),
            "data": data
        }
        await self.send_message(topic, message)

    async def publish_rpc_request(self, func_name: str, args: Dict[str, Any], request_id: str):
        """Publish an RPC request to the appropriate topic."""
        topic = f"{self.kafka_config.topic_prefix}rpc_requests"
        message = {
            "func_name": func_name,
            "args": args,
            "request_id": request_id,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_message(topic, message)

    async def publish_rpc_response(self, request_id: str, result: Any, error: Optional[str] = None):
        """Publish an RPC response to the appropriate topic."""
        topic = f"{self.kafka_config.topic_prefix}rpc_responses"
        message = {
            "request_id": request_id,
            "result": result,
            "error": error,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_message(topic, message)

    async def broadcast_message(self, message: Dict[str, Any], broadcast_id: str):
        """Broadcast a message to all modules."""
        topic = f"{self.kafka_config.topic_prefix}broadcast"
        broadcast_msg = {
            "broadcast_id": broadcast_id,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_message(topic, broadcast_msg)

    async def subscribe_to_broadcasts(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to broadcast messages."""
        topic = f"{self.kafka_config.topic_prefix}broadcast"
        await self.consume_messages(topic, callback)