"""
Qyro Python Adapter v2 - Enhanced with RPC Support

This module provides the Qyro API for Python services, including:
- Shared state (Redis)
- Event streaming (Kafka)
- Cross-language RPC (@expose decorator)
"""

import os
import json
import atexit
from typing import Any, Callable, Generator, TypeVar

# Configuration from environment variables
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
SERVICE_NAME = os.environ.get("QYRO_SERVICE_NAME", "python-service")

# Type variable for generic decoration
F = TypeVar('F', bound=Callable[..., Any])

# Lazy-loaded connections
_redis = None
_producer = None


def _get_redis():
    """Lazy-load Redis connection."""
    global _redis
    if _redis is None:
        import redis
        _redis = redis.Redis(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            decode_responses=True
        )
    return _redis


def _get_producer():
    """Lazy-load Kafka producer."""
    global _producer
    if _producer is None:
        from kafka import KafkaProducer
        _producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    return _producer


# =============================================================================
# Shared State API (Redis)
# =============================================================================

def set(key: str, value: Any) -> None:
    """
    Set a value in shared memory (Redis).
    
    Args:
        key: The key to store the value under
        value: The value to store (dict/list will be JSON serialized)
        
    Example:
        qyro.set("user:123", {"name": "John", "age": 30})
    """
    r = _get_redis()
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    r.set(key, value)


def get(key: str) -> Any:
    """
    Get a value from shared memory (Redis).
    
    Args:
        key: The key to retrieve
        
    Returns:
        The stored value, or None if not found
        
    Example:
        user = qyro.get("user:123")
    """
    r = _get_redis()
    val = r.get(key)
    if val is None:
        return None
    try:
        return json.loads(val)
    except (TypeError, json.JSONDecodeError):
        return val


def delete(key: str) -> bool:
    """
    Delete a key from shared memory.
    
    Args:
        key: The key to delete
        
    Returns:
        True if the key was deleted, False if it didn't exist
    """
    r = _get_redis()
    return r.delete(key) > 0


def exists(key: str) -> bool:
    """
    Check if a key exists in shared memory.
    
    Args:
        key: The key to check
        
    Returns:
        True if the key exists
    """
    r = _get_redis()
    return r.exists(key) > 0


def incr(key: str, amount: int = 1) -> int:
    """
    Increment a counter in shared memory.
    
    Args:
        key: The key to increment
        amount: Amount to increment by (default 1)
        
    Returns:
        The new value after increment
    """
    r = _get_redis()
    return r.incrby(key, amount)


def expire(key: str, seconds: int) -> bool:
    """
    Set an expiration time on a key.
    
    Args:
        key: The key to expire
        seconds: TTL in seconds
        
    Returns:
        True if the expiration was set
    """
    r = _get_redis()
    return r.expire(key, seconds)


# =============================================================================
# Event Streaming API (Kafka)
# =============================================================================

def publish(topic: str, message: dict) -> None:
    """
    Publish a message to a topic (Kafka).
    
    Args:
        topic: The topic name
        message: The message to publish (will be JSON serialized)
        
    Example:
        qyro.publish("orders", {"order_id": 123, "status": "created"})
    """
    producer = _get_producer()
    producer.send(topic, message)
    producer.flush()


def subscribe(topic: str, group_id: str = None) -> Generator[dict, None, None]:
    """
    Subscribe to a topic and yield messages (Kafka).
    
    Args:
        topic: The topic to subscribe to
        group_id: Consumer group ID (optional)
        
    Yields:
        dict: Each message from the topic
        
    Example:
        for message in qyro.subscribe("orders"):
            print(f"Received: {message}")
    """
    from kafka import KafkaConsumer
    
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=group_id or f"qyro-{SERVICE_NAME}",
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    for message in consumer:
        yield message.value


# =============================================================================
# Cross-Language RPC API
# =============================================================================

# Import RPC components
try:
    from qyro.core.rpc import (
        expose,
        call,
        call_async,
        start_server,
        list_exposed_functions,
        registry
    )
    _rpc_available = True
except ImportError:
    _rpc_available = False
    
    # Fallback implementations when RPC module not available
    def expose(func: F = None, *, name: str = None) -> F:
        """Decorator to expose a function for RPC (fallback - no-op)."""
        def decorator(f):
            return f
        return decorator if func is None else decorator(func)
    
    def call(function_path: str, *args, **kwargs) -> Any:
        """Call a remote function (fallback - raises error)."""
        raise RuntimeError(
            "RPC not available. Make sure qyro.core.rpc is installed."
        )
    
    def call_async(function_path: str, *args, **kwargs):
        """Async call (fallback - raises error)."""
        raise RuntimeError("RPC not available.")
    
    def start_server():
        """Start RPC server (fallback - no-op)."""
        pass
    
    def list_exposed_functions():
        """List exposed functions (fallback - empty list)."""
        return []


# =============================================================================
# Utility Functions
# =============================================================================

def log(message: str, level: str = "INFO") -> None:
    """
    Log a message with proper formatting.
    
    Args:
        message: The message to log
        level: Log level (INFO, WARN, ERROR, DEBUG)
    """
    import sys
    from datetime import datetime
    
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] [{level}] [{SERVICE_NAME}] {message}", flush=True)
    sys.stdout.flush()


def info(message: str) -> None:
    """Log an info message."""
    log(message, "INFO")


def warn(message: str) -> None:
    """Log a warning message."""
    log(message, "WARN")


def error(message: str) -> None:
    """Log an error message."""
    log(message, "ERROR")


def debug(message: str) -> None:
    """Log a debug message."""
    log(message, "DEBUG")


# =============================================================================
# Service Discovery
# =============================================================================

def register_service(metadata: dict = None) -> None:
    """
    Register this service for discovery.
    
    Args:
        metadata: Additional service metadata
    """
    service_info = {
        "name": SERVICE_NAME,
        "host": os.environ.get("HOSTNAME", "localhost"),
        "functions": list_exposed_functions(),
        **(metadata or {})
    }
    set(f"qyro:service:{SERVICE_NAME}", service_info)
    info(f"Service registered: {SERVICE_NAME}")


def discover_services() -> dict:
    """
    Discover all registered Qyro services.
    
    Returns:
        dict: Service name -> service info
    """
    r = _get_redis()
    services = {}
    
    for key in r.scan_iter("qyro:service:*"):
        service_name = key.replace("qyro:service:", "")
        services[service_name] = get(key)
    
    return services


def discover_function(function_path: str) -> dict:
    """
    Get metadata about a function from another service.
    
    Args:
        function_path: Full function path like "api.calculate"
        
    Returns:
        dict: Function metadata or None if not found
    """
    parts = function_path.split(".", 1)
    if len(parts) != 2:
        return None
    
    service_name, func_name = parts
    service_info = get(f"qyro:service:{service_name}")
    
    if not service_info:
        return None
    
    for func in service_info.get("functions", []):
        if func.get("local_name") == func_name or func.get("full_name") == function_path:
            return func
    
    return None


# =============================================================================
# Cleanup
# =============================================================================

def _cleanup():
    """Cleanup connections on exit."""
    global _redis, _producer
    
    if _redis is not None:
        try:
            _redis.close()
        except:
            pass
    
    if _producer is not None:
        try:
            _producer.close()
        except:
            pass


atexit.register(_cleanup)


# =============================================================================
# Module Info
# =============================================================================

__version__ = "2.0.0"
__all__ = [
    # State
    "set", "get", "delete", "exists", "incr", "expire",
    # Events
    "publish", "subscribe",
    # RPC
    "expose", "call", "call_async", "start_server",
    # Discovery
    "register_service", "discover_services", "discover_function",
    # Logging
    "log", "info", "warn", "error", "debug",
]
