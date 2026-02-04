"""
Redis-based Memory System for Qyro

This module provides a Redis-backed shared memory implementation with pub/sub
for real-time communication between Qyro modules. It replaces the old file-based
memory system with a more scalable and performant solution.

Features:
- Redis pub/sub for real-time state change notifications
- Thread-safe operations with connection pooling
- Automatic reconnection for transient failures
- Module state management
- Event broadcasting system
"""

import json
import threading
import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import redis
    from redis import Redis, ConnectionPool
    from redis.exceptions import (
        ConnectionError as RedisConnectionError,
        TimeoutError as RedisTimeoutError,
        RedisError
    )
except ImportError:
    raise ImportError(
        "redis library is required. Install with: pip install redis>=5.0.0"
    )

from .errors import QyroError, MemoryError, ErrorCode, Result
from .logging import get_logger

logger = get_logger("qyro.redis_memory")


# Redis key and channel constants
class RedisKeys:
    """Redis key and channel name constants."""
    # State storage
    STATE = "qyro:state"
    STATE_CHANGED = "qyro:state:changed"

    # Broadcasting
    BROADCAST = "qyro:broadcast"

    # Events
    EVENTS = "qyro:events"

    # Module registry
    MODULE_REGISTRY = "qyro:modules:registry"
    MODULE_STATE_PREFIX = "qyro:modules:state:"

    # Statistics
    STATS = "qyro:stats"


class EventType(Enum):
    """Standard event types for Qyro system."""
    MODULE_REGISTERED = "module_registered"
    MODULE_UNREGISTERED = "module_unregistered"
    MODULE_STATE_CHANGED = "module_state_changed"
    STATE_CHANGED = "state_changed"
    BROADCAST = "broadcast"
    ERROR = "error"
    INFO = "info"


@dataclass
class QyroEvent:
    """Structured event for Redis pub/sub."""
    event_type: str
    data: Dict[str, Any]
    timestamp: float
    source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QyroEvent':
        """Create event from dictionary."""
        return cls(**data)


@dataclass
class ModuleMetadata:
    """Metadata for registered modules."""
    name: str
    version: str
    language: str
    pid: Optional[int] = None
    registered_at: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModuleMetadata':
        """Create metadata from dictionary."""
        return cls(**data)


class RedisConnectionError(QyroError):
    """Redis connection error."""
    def __init__(self, message: str = "Redis connection error"):
        super().__init__(ErrorCode.MEMORY_NOT_FOUND, message)


class RedisQyroMemory:
    """
    Redis-based shared memory with pub/sub for real-time communication.

    This class provides a thread-safe interface to Redis for storing and
    sharing state across Qyro modules. It uses Redis pub/sub for real-time
    notifications of state changes.

    Redis Keys:
        qyro:state - Main state storage (hash)
        qyro:state:changed - Channel for state change notifications
        qyro:broadcast - Channel for broadcasting messages
        qyro:events - Channel for general events
        qyro:modules:registry - Set of registered module names
        qyro:modules:state:{module_name} - State for specific modules

    Example:
        >>> memory = RedisQyroMemory(host='localhost', port=6379)
        >>> memory.write({'counter': 0, 'status': 'active'})
        >>> state = memory.read()
        >>> memory.subscribe_to_changes(lambda data: print(f"State changed: {data}"))
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        max_connections: int = 50,
        retry_on_timeout: bool = True,
        decode_responses: bool = True
    ):
        """
        Initialize Redis connection with connection pooling.
        """
        import os

        # Respect environment variables if arguments are defaults
        if host == 'localhost':
            host = os.environ.get('QYRO_REDIS_HOST', 'localhost')

        if port == 6379:
            port_str = os.environ.get('QYRO_REDIS_PORT')
            if port_str:
                try:
                    port = int(port_str)
                except ValueError:
                    pass

        self.host = host
        self.port = port

        self.db = db
        self.password = password

        # Thread safety
        self._lock = threading.RLock()
        self._write_lock = threading.Lock()

        # Subscription management
        self._pubsub_thread: Optional[threading.Thread] = None
        self._pubsub_running = threading.Event()
        self._state_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._event_callbacks: List[Callable[[QyroEvent], None]] = []

        # Reconnection settings
        self._max_retries = 3
        self._retry_delay = 1.0
        self._connected = False

        # Initialize connection pools - separate for commands and pubsub
        try:
            self._command_pool = ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                max_connections=max_connections,
                retry_on_timeout=retry_on_timeout,
                decode_responses=decode_responses,
                health_check_interval=30  # Health check every 30 seconds
            )

            # Create Redis clients using pools
            self._redis = Redis(connection_pool=self._command_pool)

            # Separate pool for pubsub connections
            self._pubsub_pool = ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                max_connections=5,  # Smaller pool for pubsub
                retry_on_timeout=retry_on_timeout,
                decode_responses=decode_responses
            )

            # Test connection
            self._test_connection()
            self._connected = True

            logger.info(
                "redis_memory_initialized",
                host=host,
                port=port,
                db=db
            )

        except RedisConnectionError as e:
            logger.error("redis_connection_failed", error=str(e))
            raise RedisConnectionError(
                f"Failed to connect to Redis at {host}:{port}: {e}"
            )
        except Exception as e:
            logger.error("redis_init_failed", error=str(e))
            raise RedisConnectionError(
                f"Failed to initialize Redis memory: {e}"
            )
    
    def _test_connection(self) -> None:
        """
        Test Redis connection with retry logic.
        
        Raises:
            RedisConnectionError: If connection fails after retries
        """
        for attempt in range(self._max_retries):
            try:
                self._redis.ping()
                return
            except (RedisConnectionError, RedisTimeoutError) as e:
                if attempt < self._max_retries - 1:
                    logger.warning(
                        "redis_connection_retry",
                        attempt=attempt + 1,
                        max_retries=self._max_retries,
                        error=str(e)
                    )
                    time.sleep(self._retry_delay * (attempt + 1))
                else:
                    raise
    
    def _ensure_connection(self) -> None:
        """
        Ensure Redis connection is active, reconnect if necessary.
        
        This method is called before each operation to handle transient
        connection failures gracefully.
        """
        try:
            self._redis.ping()
        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.warning("redis_connection_lost", error=str(e))
            try:
                self._test_connection()
                logger.info("redis_connection_restored")
            except Exception as reconnect_error:
                logger.error("redis_reconnection_failed", error=str(reconnect_error))
                raise RedisConnectionError(
                    f"Failed to reconnect to Redis: {reconnect_error}"
                )
    
    def read(self) -> Dict[str, Any]:
        """
        Read the current state from Redis.

        Returns:
            Dictionary containing the current state. Returns empty dict
            if no state exists.

        Raises:
            RedisConnectionError: If Redis connection fails
        """
        with self._lock:
            self._ensure_connection()

            try:
                # Read state from hash
                state_data = self._redis.hgetall(RedisKeys.STATE)

                if not state_data:
                    logger.debug("redis_state_empty")
                    return {}

                # Parse JSON values
                state = {}
                for key, value in state_data.items():
                    try:
                        state[key] = json.loads(value)
                    except json.JSONDecodeError:
                        state[key] = value

                logger.debug("redis_state_read", keys=list(state.keys()))
                return state

            except RedisError as e:
                logger.error("redis_read_failed", error=str(e))
                raise RedisConnectionError(f"Failed to read state: {e}")

    def read_field(self, key: str) -> Any:
        """
        Read a specific field from the state without loading the entire state.

        Args:
            key: Field name to read

        Returns:
            Value of the field, or None if not found
        """
        with self._lock:
            self._ensure_connection()

            try:
                value = self._redis.hget(RedisKeys.STATE, key)
                if value is None:
                    return None

                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value

            except RedisError as e:
                logger.error("redis_read_field_failed", error=str(e), key=key)
                raise RedisConnectionError(f"Failed to read field {key}: {e}")

    def read_fields(self, keys: List[str]) -> Dict[str, Any]:
        """
        Read multiple specific fields from the state without loading the entire state.

        Args:
            keys: List of field names to read

        Returns:
            Dictionary containing the requested fields
        """
        with self._lock:
            self._ensure_connection()

            try:
                values = self._redis.hmget(RedisKeys.STATE, keys)
                result = {}

                for i, key in enumerate(keys):
                    value = values[i]
                    if value is not None:
                        try:
                            result[key] = json.loads(value)
                        except json.JSONDecodeError:
                            result[key] = value

                logger.debug("redis_fields_read", keys=keys)
                return result

            except RedisError as e:
                logger.error("redis_read_fields_failed", error=str(e), keys=keys)
                raise RedisConnectionError(f"Failed to read fields {keys}: {e}")
    
    def write(self, data: Dict[str, Any]) -> None:
        """
        Write state to Redis and publish change notification.

        This method writes the provided data to Redis and publishes a
        notification on the state change channel. All subscribers will
        receive the new state.

        Args:
            data: Dictionary containing state to write

        Raises:
            RedisConnectionError: If Redis connection fails
            ValueError: If data is not a dictionary
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        with self._write_lock:
            self._ensure_connection()

            try:
                # Use pipeline for atomic operation
                with self._redis.pipeline() as pipe:
                    # Write new state as hash (Partial Update) - DO NOT DELETE FIRST
                    if data:
                        serialized_data = {
                            key: json.dumps(value) if not isinstance(value, str) else value
                            for key, value in data.items()
                        }
                        # Use HSET to update specific fields without affecting others
                        pipe.hset(RedisKeys.STATE, mapping=serialized_data)

                    # Publish state change notification
                    notification = json.dumps({
                        'timestamp': time.time(),
                        'keys': list(data.keys()) if data else []
                    })
                    pipe.publish(RedisKeys.STATE_CHANGED, notification)

                    # Execute pipeline
                    pipe.execute()

                logger.debug("redis_state_written", keys=list(data.keys()) if data else [])

            except RedisError as e:
                logger.error("redis_write_failed", error=str(e))
                raise RedisConnectionError(f"Failed to write state: {e}")

    def update_field(self, key: str, value: Any) -> None:
        """
        Update a single field in the state without affecting other fields.

        Args:
            key: Field name to update
            value: Value to set for the field

        Raises:
            RedisConnectionError: If Redis connection fails
        """
        with self._write_lock:
            self._ensure_connection()

            try:
                # Serialize the value
                serialized_value = json.dumps(value) if not isinstance(value, str) else value

                # Update only the specific field
                self._redis.hset(RedisKeys.STATE, key, serialized_value)

                # Publish state change notification
                notification = json.dumps({
                    'timestamp': time.time(),
                    'keys': [key]
                })
                self._redis.publish(RedisKeys.STATE_CHANGED, notification)

                logger.debug("redis_field_updated", key=key)

            except RedisError as e:
                logger.error("redis_field_update_failed", error=str(e))
                raise RedisConnectionError(f"Failed to update field: {e}")

    def update_fields(self, data: Dict[str, Any]) -> None:
        """
        Update multiple fields in the state without affecting other fields.

        Args:
            data: Dictionary containing fields to update

        Raises:
            RedisConnectionError: If Redis connection fails
            ValueError: If data is not a dictionary
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        with self._write_lock:
            self._ensure_connection()

            try:
                # Use pipeline for atomic operation
                with self._redis.pipeline() as pipe:
                    # Update specific fields without affecting others
                    if data:
                        serialized_data = {
                            key: json.dumps(value) if not isinstance(value, str) else value
                            for key, value in data.items()
                        }
                        pipe.hset(RedisKeys.STATE, mapping=serialized_data)

                    # Publish state change notification
                    notification = json.dumps({
                        'timestamp': time.time(),
                        'keys': list(data.keys()) if data else []
                    })
                    pipe.publish(RedisKeys.STATE_CHANGED, notification)

                    # Execute pipeline
                    pipe.execute()

                logger.debug("redis_fields_updated", keys=list(data.keys()) if data else [])

            except RedisError as e:
                logger.error("redis_fields_update_failed", error=str(e))
                raise RedisConnectionError(f"Failed to update fields: {e}")
    
    def subscribe_to_changes(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to state change notifications.
        
        This method starts a background thread that listens for state
        change notifications and invokes the provided callback when
        changes occur.
        
        Args:
            callback: Function to call when state changes. Receives the
                     new state as a dictionary.
        
        Note:
            Multiple callbacks can be registered. Each will be called
            when a state change occurs.
        """
        with self._lock:
            if callback in self._state_callbacks:
                logger.warning("callback_already_registered")
                return
            
            self._state_callbacks.append(callback)
            
            # Start pub/sub thread if not already running
            if not self._pubsub_running.is_set():
                self._start_pubsub_thread()
            
            logger.info("state_change_subscribed", callbacks=len(self._state_callbacks))
    
    def _start_pubsub_thread(self) -> None:
        """Start the background pub/sub listener thread."""
        if self._pubsub_running.is_set():
            return
        
        self._pubsub_running.set()
        self._pubsub_thread = threading.Thread(
            target=self._pubsub_listener,
            daemon=True,
            name="RedisPubSubListener"
        )
        self._pubsub_thread.start()
        logger.info("pubsub_thread_started")
    
    def _pubsub_listener(self) -> None:
        """
        Background thread that listens for pub/sub messages.

        This thread runs in the background and processes messages from
        Redis pub/sub channels. It handles both state changes and
        general events.
        """
        # Create separate connection for pub/sub using dedicated pool
        pubsub_redis = Redis(connection_pool=self._pubsub_pool)
        pubsub = pubsub_redis.pubsub()

        # Subscribe to channels
        pubsub.subscribe(RedisKeys.STATE_CHANGED)
        pubsub.subscribe(RedisKeys.EVENTS)

        logger.info("pubsub_listener_started")

        try:
            while self._pubsub_running.is_set():
                try:
                    # Get message with timeout
                    message = pubsub.get_message(timeout=1.0)

                    if message is None:
                        continue

                    if message['type'] == 'message':
                        channel = message['channel']
                        data = message['data']

                        if channel == RedisKeys.STATE_CHANGED:
                            self._handle_state_change(data)
                        elif channel == RedisKeys.EVENTS:
                            self._handle_event(data)

                except (RedisConnectionError, RedisTimeoutError) as e:
                    logger.warning("pubsub_connection_error", error=str(e))
                    time.sleep(1.0)
                except Exception as e:
                    logger.error("pubsub_listener_error", error=str(e))
                    time.sleep(1.0)

        finally:
            pubsub.close()
            logger.info("pubsub_listener_stopped")
    
    def _handle_state_change(self, data: str) -> None:
        """
        Handle state change notification.
        
        Args:
            data: JSON-encoded notification data
        """
        try:
            notification = json.loads(data)
            state = self.read()
            
            # Call all registered callbacks
            for callback in self._state_callbacks:
                try:
                    callback(state)
                except Exception as e:
                    logger.error("state_callback_error", error=str(e))
            
            logger.debug("state_change_handled", notification=notification)
            
        except json.JSONDecodeError as e:
            logger.error("state_change_decode_error", error=str(e))
    
    def _handle_event(self, data: str) -> None:
        """
        Handle general event notification.

        Args:
            data: JSON-encoded event data
        """
        try:
            event_dict = json.loads(data)
            event = QyroEvent.from_dict(event_dict)

            # Call all registered event callbacks
            for callback in self._event_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.error("event_callback_error", error=str(e))

            logger.debug("event_handled", event_type=event.event_type)

        except json.JSONDecodeError as e:
            logger.error("event_decode_error", error=str(e))
    
    def publish_event(self, event_type: str, data: Dict[str, Any], source: Optional[str] = None) -> None:
        """
        Publish an event to the events channel.

        Args:
            event_type: Type of event (e.g., 'module_registered', 'error')
            data: Event data payload
            source: Optional source identifier

        Raises:
            RedisConnectionError: If Redis connection fails
        """
        self._ensure_connection()

        try:
            event = QyroEvent(
                event_type=event_type,
                data=data,
                timestamp=time.time(),
                source=source
            )

            self._redis.publish(RedisKeys.EVENTS, json.dumps(event.to_dict()))

            logger.debug("event_published", event_type=event_type)

        except RedisError as e:
            logger.error("event_publish_failed", error=str(e))
            raise RedisConnectionError(f"Failed to publish event: {e}")
    
    def subscribe_to_events(self, callback: Callable[[QyroEvent], None]) -> None:
        """
        Subscribe to general events.

        Args:
            callback: Function to call when events are received. Receives
                     a QyroEvent object.
        """
        with self._lock:
            if callback in self._event_callbacks:
                logger.warning("event_callback_already_registered")
                return

            self._event_callbacks.append(callback)

            # Start pub/sub thread if not already running
            if not self._pubsub_running.is_set():
                self._start_pubsub_thread()

            logger.info("events_subscribed", callbacks=len(self._event_callbacks))
    
    def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all modules.
        
        Args:
            message: Message to broadcast
        
        Raises:
            RedisConnectionError: If Redis connection fails
        """
        self._ensure_connection()
        
        try:
            self._redis.publish(RedisKeys.BROADCAST, json.dumps(message))
            logger.debug("message_broadcast")
            
        except RedisError as e:
            logger.error("broadcast_failed", error=str(e))
            raise RedisConnectionError(f"Failed to broadcast message: {e}")
    
    def subscribe_to_broadcasts(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to broadcast messages.

        Args:
            callback: Function to call when broadcasts are received
        """
        # Create separate pubsub connection for broadcasts using dedicated pool
        pubsub_redis = Redis(connection_pool=self._pubsub_pool)
        pubsub = pubsub_redis.pubsub()
        pubsub.subscribe(RedisKeys.BROADCAST)

        def broadcast_listener():
            try:
                for message in pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            callback(data)
                        except json.JSONDecodeError as e:
                            logger.error("broadcast_decode_error", error=str(e))
            except Exception as e:
                logger.error("broadcast_listener_error", error=str(e))
            finally:
                pubsub.close()

        thread = threading.Thread(target=broadcast_listener, daemon=True)
        thread.start()
        logger.info("broadcast_subscribed")
    
    def set_module_state(self, module_name: str, state: Dict[str, Any]) -> None:
        """
        Set state for a specific module.
        
        Args:
            module_name: Name of the module
            state: Module state dictionary
        
        Raises:
            RedisConnectionError: If Redis connection fails
        """
        self._ensure_connection()
        
        try:
            key = f"{RedisKeys.MODULE_STATE_PREFIX}{module_name}"
            self._redis.set(key, json.dumps(state))
            
            # Publish module state change event
            self.publish_event(
                EventType.MODULE_STATE_CHANGED.value,
                {'module': module_name, 'state': state},
                source=module_name
            )
            
            logger.debug("module_state_set", module=module_name)
            
        except RedisError as e:
            logger.error("module_state_set_failed", error=str(e))
            raise RedisConnectionError(f"Failed to set module state: {e}")
    
    def get_module_state(self, module_name: str) -> Dict[str, Any]:
        """
        Get state for a specific module.
        
        Args:
            module_name: Name of the module
        
        Returns:
            Module state dictionary. Returns empty dict if module has no state.
        
        Raises:
            RedisConnectionError: If Redis connection fails
        """
        self._ensure_connection()
        
        try:
            key = f"{RedisKeys.MODULE_STATE_PREFIX}{module_name}"
            data = self._redis.get(key)
            
            if data is None:
                return {}
            
            return json.loads(data)
            
        except RedisError as e:
            logger.error("module_state_get_failed", error=str(e))
            raise RedisConnectionError(f"Failed to get module state: {e}")
        except json.JSONDecodeError as e:
            logger.error("module_state_decode_error", error=str(e))
            return {}
    
    def register_module(self, module_name: str, metadata: Dict[str, Any]) -> None:
        """
        Register a module with the system.
        
        Args:
            module_name: Name of the module
            metadata: Module metadata (version, language, pid, etc.)
        
        Raises:
            RedisConnectionError: If Redis connection fails
        """
        self._ensure_connection()
        
        try:
            # Create module metadata
            module_metadata = ModuleMetadata(
                name=module_name,
                version=metadata.get('version', '1.0.0'),
                language=metadata.get('language', 'unknown'),
                pid=metadata.get('pid'),
                registered_at=time.time(),
                metadata=metadata.get('metadata', {})
            )
            
            # Add to registry
            self._redis.sadd(RedisKeys.MODULE_REGISTRY, module_name)
            
            # Store metadata
            metadata_key = f"{RedisKeys.MODULE_STATE_PREFIX}{module_name}:metadata"
            self._redis.set(metadata_key, json.dumps(module_metadata.to_dict()))
            
            # Publish registration event
            self.publish_event(
                EventType.MODULE_REGISTERED.value,
                module_metadata.to_dict(),
                source=module_name
            )
            
            logger.info("module_registered", module=module_name, metadata=metadata)
            
        except RedisError as e:
            logger.error("module_register_failed", error=str(e))
            raise RedisConnectionError(f"Failed to register module: {e}")
    
    def unregister_module(self, module_name: str) -> None:
        """
        Unregister a module from the system.
        
        Args:
            module_name: Name of the module
        
        Raises:
            RedisConnectionError: If Redis connection fails
        """
        self._ensure_connection()
        
        try:
            # Remove from registry
            self._redis.srem(RedisKeys.MODULE_REGISTRY, module_name)
            
            # Remove metadata
            metadata_key = f"{RedisKeys.MODULE_STATE_PREFIX}{module_name}:metadata"
            self._redis.delete(metadata_key)
            
            # Remove state
            state_key = f"{RedisKeys.MODULE_STATE_PREFIX}{module_name}"
            self._redis.delete(state_key)
            
            # Publish unregistration event
            self.publish_event(
                EventType.MODULE_UNREGISTERED.value,
                {'module': module_name},
                source=module_name
            )
            
            logger.info("module_unregistered", module=module_name)
            
        except RedisError as e:
            logger.error("module_unregister_failed", error=str(e))
            raise RedisConnectionError(f"Failed to unregister module: {e}")
    
    def get_registered_modules(self) -> List[str]:
        """
        Get list of registered modules.
        
        Returns:
            List of module names
        
        Raises:
            RedisConnectionError: If Redis connection fails
        """
        self._ensure_connection()
        
        try:
            modules = self._redis.smembers(RedisKeys.MODULE_REGISTRY)
            return sorted(list(modules)) if modules else []
            
        except RedisError as e:
            logger.error("get_modules_failed", error=str(e))
            raise RedisConnectionError(f"Failed to get registered modules: {e}")
    
    def get_module_metadata(self, module_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific module.
        
        Args:
            module_name: Name of the module
        
        Returns:
            Module metadata dictionary or None if not found
        """
        self._ensure_connection()
        
        try:
            metadata_key = f"{RedisKeys.MODULE_STATE_PREFIX}{module_name}:metadata"
            data = self._redis.get(metadata_key)
            
            if data is None:
                return None
            
            return json.loads(data)
            
        except RedisError as e:
            logger.error("get_module_metadata_failed", error=str(e))
            return None
        except json.JSONDecodeError:
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory and Redis statistics.
        
        Returns:
            Dictionary containing statistics about the Redis memory system
        """
        self._ensure_connection()
        
        try:
            # Get Redis info
            info = self._redis.info()
            
            # Get state size
            state_size = self._redis.hlen(RedisKeys.STATE)
            
            # Get module count
            module_count = self._redis.scard(RedisKeys.MODULE_REGISTRY)
            
            # Get connection pool stats
            pool_stats = {
                'max_connections': self._pool.max_connections,
                'created_connections': self._pool.created_connections,
                'available_connections': self._pool._available_connections if hasattr(self._pool, '_available_connections') else 0
            }
            
            return {
                'redis': {
                    'host': self.host,
                    'port': self.port,
                    'db': self.db,
                    'connected': self._connected,
                    'memory_used': info.get('used_memory_human', 'N/A'),
                    'total_keys': info.get('db0', {}).get('keys', 0) if 'db0' in info else 0
                },
                'state': {
                    'keys': state_size,
                    'modules': module_count
                },
                'connection_pool': pool_stats,
                'subscriptions': {
                    'state_callbacks': len(self._state_callbacks),
                    'event_callbacks': len(self._event_callbacks),
                    'pubsub_running': self._pubsub_running.is_set()
                }
            }
            
        except RedisError as e:
            logger.error("get_stats_failed", error=str(e))
            return {
                'error': str(e),
                'connected': False
            }
    
    def clear_state(self) -> None:
        """
        Clear all state from Redis.
        
        This removes the main state but preserves module registry and
        module states.
        
        Raises:
            RedisConnectionError: If Redis connection fails
        """
        self._ensure_connection()
        
        try:
            self._redis.delete(RedisKeys.STATE)
            logger.info("state_cleared")
            
        except RedisError as e:
            logger.error("clear_state_failed", error=str(e))
            raise RedisConnectionError(f"Failed to clear state: {e}")
    
    def clear_all(self) -> None:
        """
        Clear all Qyro data from Redis.

        This removes all state, module registry, and module states.
        Use with caution!

        Raises:
            RedisConnectionError: If Redis connection fails
        """
        self._ensure_connection()

        try:
            # Get all Qyro keys
            keys = self._redis.keys('qyro:*')

            if keys:
                self._redis.delete(*keys)

            logger.info("all_data_cleared", keys_deleted=len(keys) if keys else 0)

        except RedisError as e:
            logger.error("clear_all_failed", error=str(e))
            raise RedisConnectionError(f"Failed to clear all data: {e}")
    
    def close(self) -> None:
        """
        Close Redis connections and cleanup resources.

        This method stops the pub/sub listener thread and closes
        all Redis connections.
        """
        with self._lock:
            # Stop pub/sub thread
            if self._pubsub_running.is_set():
                self._pubsub_running.clear()

                # Wait for thread to finish (with timeout)
                if self._pubsub_thread and self._pubsub_thread.is_alive():
                    self._pubsub_thread.join(timeout=2.0)

            # Clear callbacks
            self._state_callbacks.clear()
            self._event_callbacks.clear()

            # Close connection pools
            try:
                if hasattr(self._command_pool, 'disconnect'):
                    self._command_pool.disconnect()
                if hasattr(self._pubsub_pool, 'disconnect'):
                    self._pubsub_pool.disconnect()
                logger.info("redis_connections_closed")
            except Exception as e:
                logger.error("close_connections_failed", error=str(e))

            # Explicitly clean up Redis client references
            self._redis = None
            self._pubsub_thread = None

            self._connected = False
            logger.info("redis_memory_closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
    
    def __del__(self):
        """Destructor to ensure connections are closed."""
        try:
            self.close()
        except Exception:
            pass


# Convenience function for creating a memory instance
def create_redis_memory(
    host: str = 'localhost',
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None
) -> RedisQyroMemory:
    """
    Create a RedisQyroMemory instance with default settings.

    Args:
        host: Redis server hostname
        port: Redis server port
        db: Redis database number
        password: Redis password (optional)

    Returns:
        Configured RedisQyroMemory instance
    """
    return RedisQyroMemory(host=host, port=port, db=db, password=password)
