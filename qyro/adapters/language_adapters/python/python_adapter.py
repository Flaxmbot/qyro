"""
Nexus Python Adapter - Redis Pub/Sub Implementation
Thread-safe Redis-based communication for cross-language integration.

This adapter uses Redis pub/sub for real-time communication instead of
file-based shared memory. It reads Redis connection info from environment
variables provided by the orchestrator.

Environment Variables:
    NEXUS_REDIS_HOST - Redis server host (default: localhost)
    NEXUS_REDIS_PORT - Redis server port (default: 6379)
    NEXUS_REDIS_DB - Redis database number (default: 0)
    NEXUS_REDIS_PASSWORD - Redis password (optional)
    NEXUS_MODULE_NAME - Module name for this adapter (required)

Redis Channels:
    nexus:state - Read/write state
    nexus:state:changed - Subscribe to state changes
    nexus:events - Publish/subscribe to events
    nexus:broadcast - Broadcast messages
"""

import os
import json
import time
import threading
import uuid
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass

try:
    import redis
except ImportError:
    raise ImportError(
        "Redis library is required. Install with: pip install redis"
    )


# Error codes matching Python constants.py
class NexusError(Exception):
    """Base exception for Nexus errors."""
    pass


class ErrorCode:
    OK = 0
    REDIS_CONNECTION_FAILED = 1001
    REDIS_SUBSCRIPTION_FAILED = 1002
    STATE_READ_FAILED = 1003
    STATE_WRITE_FAILED = 1004
    EVENT_PUBLISH_FAILED = 1005
    JSON_PARSE_ERROR = 2001


@dataclass
class RedisConfig:
    """Redis connection configuration."""
    host: str
    port: int
    db: int
    password: Optional[str]
    module_name: str


class NexusModule:
    """
    Nexus Python Adapter using Redis pub/sub for communication.
    
    This class provides a Redis-based interface for cross-language
    communication, replacing file-based shared memory with Redis pub/sub.
    """

    # Redis channel names
    CHANNEL_STATE = "nexus:state"
    CHANNEL_STATE_CHANGED = "nexus:state:changed"
    CHANNEL_EVENTS = "nexus:events"
    CHANNEL_BROADCAST = "nexus:broadcast"

    def __init__(self, module_name: Optional[str] = None):
        """
        Initialize the Nexus module with Redis connection.
        
        Args:
            module_name: Module name (defaults to NEXUS_MODULE_NAME env var)
        """
        self.config = self._load_config(module_name)
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self._subscribed = False
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._state_change_handlers: List[Callable] = []
        self._broadcast_handlers: List[Callable] = []
        self._listener_thread: Optional[threading.Thread] = None
        self._running = False
        self._process_id = uuid.uuid4().hex[:8]

    def _load_config(self, module_name: Optional[str]) -> RedisConfig:
        """Load Redis configuration from environment variables."""
        host = os.getenv("NEXUS_REDIS_HOST", "localhost")
        port = int(os.getenv("NEXUS_REDIS_PORT", "6379"))
        db = int(os.getenv("NEXUS_REDIS_DB", "0"))
        password = os.getenv("NEXUS_REDIS_PASSWORD")
        name = module_name or os.getenv("NEXUS_MODULE_NAME", "python_module")

        return RedisConfig(
            host=host,
            port=port,
            db=db,
            password=password,
            module_name=name
        )

    def connect(self) -> None:
        """
        Connect to Redis and initialize pub/sub.
        
        Raises:
            NexusError: If connection fails
        """
        try:
            # Create Redis client
            self.redis_client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )

            # Test connection
            self.redis_client.ping()

            # Create pub/sub instance
            self.pubsub = self.redis_client.pubsub()

            print(f"[NEXUS-Python] Connected to Redis at {self.config.host}:{self.config.port}")
            print(f"[NEXUS-Python] Module: {self.config.module_name} (PID: {self._process_id})")

        except redis.ConnectionError as e:
            raise NexusError(
                ErrorCode.REDIS_CONNECTION_FAILED,
                f"Failed to connect to Redis: {e}"
            )
        except Exception as e:
            raise NexusError(
                ErrorCode.REDIS_CONNECTION_FAILED,
                f"Unexpected error connecting to Redis: {e}"
            )

    def disconnect(self) -> None:
        """Disconnect from Redis and cleanup resources."""
        self._running = False

        if self._listener_thread:
            self._listener_thread.join(timeout=2)

        if self.pubsub:
            try:
                self.pubsub.close()
            except Exception:
                pass

        if self.redis_client:
            try:
                self.redis_client.close()
            except Exception:
                pass

        self._subscribed = False
        print("[NEXUS-Python] Disconnected from Redis")

    # ========================================================================
    # STATE OPERATIONS
    # ========================================================================

    def read_state(self) -> Dict[str, Any]:
        """
        Read the current state from Redis.
        
        Returns:
            Dictionary containing the current state
            
        Raises:
            NexusError: If read fails
        """
        if not self.redis_client:
            raise NexusError(
                ErrorCode.STATE_READ_FAILED,
                "Not connected to Redis"
            )

        try:
            state_json = self.redis_client.get(self.CHANNEL_STATE)
            if state_json is None:
                return {}

            return json.loads(state_json)

        except json.JSONDecodeError as e:
            raise NexusError(
                ErrorCode.JSON_PARSE_ERROR,
                f"Failed to parse state JSON: {e}"
            )
        except Exception as e:
            raise NexusError(
                ErrorCode.STATE_READ_FAILED,
                f"Failed to read state: {e}"
            )

    def write_state(self, state: Dict[str, Any]) -> None:
        """
        Write state to Redis and publish state change notification.
        
        Args:
            state: Dictionary containing the state to write
            
        Raises:
            NexusError: If write fails
        """
        if not self.redis_client:
            raise NexusError(
                ErrorCode.STATE_WRITE_FAILED,
                "Not connected to Redis"
            )

        try:
            state_json = json.dumps(state)

            # Write state to Redis
            self.redis_client.set(self.CHANNEL_STATE, state_json)

            # Publish state change notification
            notification = {
                "module": self.config.module_name,
                "pid": self._process_id,
                "timestamp": time.time()
            }
            self.redis_client.publish(
                self.CHANNEL_STATE_CHANGED,
                json.dumps(notification)
            )

        except Exception as e:
            raise NexusError(
                ErrorCode.STATE_WRITE_FAILED,
                f"Failed to write state: {e}"
            )

    # ========================================================================
    # EVENT OPERATIONS
    # ========================================================================

    def publish_event(self, event_type: str, data: Any) -> None:
        """
        Publish an event to the events channel.
        
        Args:
            event_type: Type of event (e.g., "function_call", "state_update")
            data: Event data (will be JSON serialized)
            
        Raises:
            NexusError: If publish fails
        """
        if not self.redis_client:
            raise NexusError(
                ErrorCode.EVENT_PUBLISH_FAILED,
                "Not connected to Redis"
            )

        try:
            event = {
                "type": event_type,
                "module": self.config.module_name,
                "pid": self._process_id,
                "timestamp": time.time(),
                "data": data
            }

            self.redis_client.publish(
                self.CHANNEL_EVENTS,
                json.dumps(event)
            )

        except Exception as e:
            raise NexusError(
                ErrorCode.EVENT_PUBLISH_FAILED,
                f"Failed to publish event: {e}"
            )

    def broadcast(self, message: Any) -> None:
        """
        Broadcast a message to all modules.
        
        Args:
            message: Message to broadcast (will be JSON serialized)
            
        Raises:
            NexusError: If broadcast fails
        """
        if not self.redis_client:
            raise NexusError(
                ErrorCode.EVENT_PUBLISH_FAILED,
                "Not connected to Redis"
            )

        try:
            broadcast_msg = {
                "module": self.config.module_name,
                "pid": self._process_id,
                "timestamp": time.time(),
                "message": message
            }

            self.redis_client.publish(
                self.CHANNEL_BROADCAST,
                json.dumps(broadcast_msg)
            )

        except Exception as e:
            raise NexusError(
                ErrorCode.EVENT_PUBLISH_FAILED,
                f"Failed to broadcast: {e}"
            )

    # ========================================================================
    # SUBSCRIPTION HANDLERS
    # ========================================================================

    def on_event(self, event_type: str) -> Callable:
        """
        Decorator to register an event handler.
        
        Args:
            event_type: Type of event to handle
            
        Returns:
            Decorator function
        """
        def decorator(handler: Callable):
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(handler)
            return handler
        return decorator

    def on_state_changed(self, handler: Callable) -> None:
        """
        Register a handler for state change events.
        
        Args:
            handler: Function to call when state changes
        """
        self._state_change_handlers.append(handler)

    def on_broadcast(self, handler: Callable) -> None:
        """
        Register a handler for broadcast messages.
        
        Args:
            handler: Function to call when broadcast received
        """
        self._broadcast_handlers.append(handler)

    # ========================================================================
    # PUB/SUB LISTENER
    # ========================================================================

    def subscribe(self) -> None:
        """
        Subscribe to Redis channels and start the listener thread.
        
        This subscribes to:
        - nexus:state:changed - State change notifications
        - nexus:events - All events
        - nexus:broadcast - Broadcast messages
        """
        if not self.pubsub:
            raise NexusError(
                ErrorCode.REDIS_SUBSCRIPTION_FAILED,
                "PubSub not initialized"
            )

        try:
            # Subscribe to channels
            self.pubsub.subscribe(
                self.CHANNEL_STATE_CHANGED,
                self.CHANNEL_EVENTS,
                self.CHANNEL_BROADCAST
            )

            self._subscribed = True
            self._running = True

            # Start listener thread
            self._listener_thread = threading.Thread(
                target=self._message_listener,
                daemon=True
            )
            self._listener_thread.start()

            print("[NEXUS-Python] Subscribed to Redis channels")

        except Exception as e:
            raise NexusError(
                ErrorCode.REDIS_SUBSCRIPTION_FAILED,
                f"Failed to subscribe: {e}"
            )

    def _message_listener(self) -> None:
        """
        Background thread that listens for Redis pub/sub messages.
        This runs in a separate thread and dispatches messages to handlers.
        """
        while self._running and self.pubsub:
            try:
                message = self.pubsub.get_message(timeout=1)
                if message and message['type'] == 'message':
                    self._dispatch_message(message)

            except Exception as e:
                print(f"[NEXUS-Python] Error in message listener: {e}")

    def _dispatch_message(self, message: Dict[str, Any]) -> None:
        """
        Dispatch a received message to the appropriate handlers.
        
        Args:
            message: Redis pub/sub message
        """
        channel = message['channel']
        data = message['data']

        try:
            payload = json.loads(data)

            # Handle state change notifications
            if channel == self.CHANNEL_STATE_CHANGED:
                for handler in self._state_change_handlers:
                    try:
                        handler(payload)
                    except Exception as e:
                        print(f"[NEXUS-Python] Error in state change handler: {e}")

            # Handle events
            elif channel == self.CHANNEL_EVENTS:
                event_type = payload.get('type')
                if event_type and event_type in self._event_handlers:
                    for handler in self._event_handlers[event_type]:
                        try:
                            handler(payload)
                        except Exception as e:
                            print(f"[NEXUS-Python] Error in event handler: {e}")

            # Handle broadcasts
            elif channel == self.CHANNEL_BROADCAST:
                for handler in self._broadcast_handlers:
                    try:
                        handler(payload)
                    except Exception as e:
                        print(f"[NEXUS-Python] Error in broadcast handler: {e}")

        except json.JSONDecodeError as e:
            print(f"[NEXUS-Python] Failed to parse message: {e}")

    # ========================================================================
    # RPC SUPPORT
    # ========================================================================

    def register_function(self, name: str, handler: Callable) -> None:
        """
        Register a function for cross-language RPC calls.
        
        Args:
            name: Function name
            handler: Function to call
        """
        # Publish function registration event
        registration = {
            "type": "function_register",
            "name": name,
            "module": self.config.module_name,
            "pid": self._process_id,
            "lang": "python"
        }
        self.publish_event("function_register", registration)
        print(f"[NEXUS-Python] Registered function: {name}")

    def call_function(self, name: str, args: List[Any], timeout: float = 30.0) -> Any:
        """
        Call a function registered in another module.
        
        Args:
            name: Function name
            args: Function arguments
            timeout: Timeout in seconds
            
        Returns:
            Function result
            
        Raises:
            NexusError: If call fails or times out
        """
        call_id = uuid.uuid4().hex[:12]

        # Publish function call event
        call_request = {
            "id": call_id,
            "fn": name,
            "args": args,
            "caller": self._process_id,
            "timestamp": time.time()
        }
        self.publish_event("function_call", call_request)

        # Wait for response (simplified - in production use a proper response queue)
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check for response in a real implementation
            time.sleep(0.05)

        raise NexusError(
            ErrorCode.EVENT_PUBLISH_FAILED,
            f"Call to {name} timed out after {timeout}s"
        )

    # ========================================================================
    # CONTEXT MANAGER
    # ========================================================================

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example usage of the Nexus Python adapter
    with NexusModule() as nexus:
        # Subscribe to channels
        nexus.subscribe()

        # Register event handlers
        @nexus.on_event("function_call")
        def handle_function_call(event):
            print(f"[NEXUS-Python] Received function call: {event}")

        nexus.on_state_changed(lambda e: print(f"[NEXUS-Python] State changed: {e}"))
        nexus.on_broadcast(lambda e: print(f"[NEXUS-Python] Broadcast: {e}"))

        # Register a function
        def my_function(args):
            return {"result": "Hello from Python!"}

        nexus.register_function("my_function", my_function)

        # Write state
        nexus.write_state({"counter": 0, "message": "Hello from Python"})

        # Read state
        state = nexus.read_state()
        print(f"[NEXUS-Python] Current state: {state}")

        # Publish an event
        nexus.publish_event("test_event", {"data": "test"})

        # Broadcast a message
        nexus.broadcast("Hello from Python module!")

        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[NEXUS-Python] Shutting down...")
