"""
Qyro RPC System - Cross-Language Function Calling via Kafka

This module provides the core infrastructure for calling functions
across different language containers using Kafka as the transport layer.
"""

import os
import json
import uuid
import time
import threading
import functools
from typing import Callable, Dict, Any, Optional, List, TypeVar, get_type_hints
from dataclasses import dataclass, asdict
from concurrent.futures import Future, ThreadPoolExecutor

# Configuration
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
SERVICE_NAME = os.environ.get("QYRO_SERVICE_NAME", "unknown")
RPC_TOPIC = "qyro.rpc.requests"
RPC_RESPONSE_TOPIC = "qyro.rpc.responses"
RPC_TIMEOUT = int(os.environ.get("QYRO_RPC_TIMEOUT", 30))

# Type variable for generic function decoration
F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class RPCRequest:
    """Represents an RPC call request."""
    request_id: str
    source_service: str
    target_service: str
    function_name: str
    args: List[Any]
    kwargs: Dict[str, Any]
    timestamp: float
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, data: str) -> 'RPCRequest':
        return cls(**json.loads(data))


@dataclass
class RPCResponse:
    """Represents an RPC call response."""
    request_id: str
    source_service: str
    success: bool
    result: Any
    error: Optional[str]
    timestamp: float
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, data: str) -> 'RPCResponse':
        return cls(**json.loads(data))


class FunctionRegistry:
    """
    Tracks all @expose decorated functions in this service.
    """
    _instance = None
    _functions: Dict[str, Callable] = {}
    _metadata: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._functions = {}
            cls._instance._metadata = {}
        return cls._instance
    
    def register(self, name: str, func: Callable, metadata: Dict[str, Any] = None):
        """Register a function for RPC calls."""
        self._functions[name] = func
        self._metadata[name] = metadata or {}
    
    def get(self, name: str) -> Optional[Callable]:
        """Get a registered function by name."""
        return self._functions.get(name)
    
    def list_functions(self) -> List[Dict[str, Any]]:
        """List all registered functions with metadata."""
        return [
            {"name": name, **self._metadata.get(name, {})}
            for name in self._functions.keys()
        ]
    
    def execute(self, name: str, args: List, kwargs: Dict) -> Any:
        """Execute a registered function."""
        func = self.get(name)
        if func is None:
            raise ValueError(f"Function '{name}' not found in registry")
        return func(*args, **kwargs)


# Global registry instance
registry = FunctionRegistry()


def expose(func: F = None, *, name: str = None) -> F:
    """
    Decorator to expose a function for cross-language RPC calls.
    
    Usage:
        @expose
        def my_function(x: int, y: int) -> int:
            return x + y
        
        @expose(name="custom_name")
        def another_function():
            pass
    """
    def decorator(f: F) -> F:
        func_name = name or f.__name__
        full_name = f"{SERVICE_NAME}.{func_name}"
        
        # Extract type hints for documentation
        hints = {}
        try:
            hints = get_type_hints(f)
        except Exception:
            pass
        
        metadata = {
            "service": SERVICE_NAME,
            "local_name": func_name,
            "full_name": full_name,
            "doc": f.__doc__ or "",
            "args": hints,
        }
        
        registry.register(full_name, f, metadata)
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        
        # Attach metadata to the wrapper
        wrapper._qyro_exposed = True
        wrapper._qyro_name = full_name
        
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator


class RPCClient:
    """
    Client for making RPC calls to other services.
    
    Usage:
        result = call("other-service.function_name", arg1, arg2, key=value)
    """
    _instance = None
    _producer = None
    _consumer = None
    _pending_requests: Dict[str, Future] = {}
    _executor: ThreadPoolExecutor = None
    _listener_thread: threading.Thread = None
    _running: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._pending_requests = {}
            cls._instance._running = False
        return cls._instance
    
    def _ensure_initialized(self):
        """Lazy initialization of Kafka connections."""
        if self._producer is not None:
            return
        
        try:
            from kafka import KafkaProducer, KafkaConsumer
            
            self._producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: v.encode('utf-8'),
                acks='all'
            )
            
            # Start response listener in background
            self._executor = ThreadPoolExecutor(max_workers=4)
            self._start_response_listener()
            
        except Exception as e:
            print(f"[Qyro RPC] Warning: Failed to initialize Kafka: {e}")
    
    def _start_response_listener(self):
        """Start background thread to listen for RPC responses."""
        if self._running:
            return
        
        self._running = True
        
        def listener():
            try:
                from kafka import KafkaConsumer
                
                consumer = KafkaConsumer(
                    RPC_RESPONSE_TOPIC,
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                    group_id=f"qyro-rpc-{SERVICE_NAME}-{uuid.uuid4().hex[:8]}",
                    auto_offset_reset='latest',
                    value_deserializer=lambda x: x.decode('utf-8'),
                    consumer_timeout_ms=1000
                )
                
                while self._running:
                    try:
                        for message in consumer:
                            response = RPCResponse.from_json(message.value)
                            
                            # Check if this response is for us
                            if response.request_id in self._pending_requests:
                                future = self._pending_requests.pop(response.request_id)
                                
                                if response.success:
                                    future.set_result(response.result)
                                else:
                                    future.set_exception(
                                        RuntimeError(f"RPC Error: {response.error}")
                                    )
                    except Exception as e:
                        if self._running:
                            time.sleep(0.1)
                            
            except Exception as e:
                print(f"[Qyro RPC] Response listener error: {e}")
        
        self._listener_thread = threading.Thread(target=listener, daemon=True)
        self._listener_thread.start()
    
    def call(self, function_path: str, *args, timeout: float = None, **kwargs) -> Any:
        """
        Call a remote function.
        
        Args:
            function_path: Full path like "service-name.function_name"
            *args: Positional arguments
            timeout: Override default timeout
            **kwargs: Keyword arguments
            
        Returns:
            The result of the remote function call
            
        Raises:
            TimeoutError: If the call times out
            RuntimeError: If the remote function raises an error
        """
        self._ensure_initialized()
        
        # Parse target service from function path
        parts = function_path.split(".", 1)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid function path '{function_path}'. "
                "Expected 'service-name.function_name'"
            )
        
        target_service, function_name = parts
        
        # Create request
        request = RPCRequest(
            request_id=str(uuid.uuid4()),
            source_service=SERVICE_NAME,
            target_service=target_service,
            function_name=function_path,
            args=list(args),
            kwargs=kwargs,
            timestamp=time.time()
        )
        
        # Create future for response
        future = Future()
        self._pending_requests[request.request_id] = future
        
        # Send request
        self._producer.send(RPC_TOPIC, request.to_json())
        self._producer.flush()
        
        # Wait for response
        try:
            return future.result(timeout=timeout or RPC_TIMEOUT)
        except TimeoutError:
            self._pending_requests.pop(request.request_id, None)
            raise TimeoutError(
                f"RPC call to '{function_path}' timed out after {timeout or RPC_TIMEOUT}s"
            )
    
    def call_async(self, function_path: str, *args, **kwargs) -> Future:
        """
        Call a remote function asynchronously.
        
        Returns a Future that can be awaited or checked later.
        """
        self._ensure_initialized()
        
        parts = function_path.split(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid function path '{function_path}'")
        
        target_service, function_name = parts
        
        request = RPCRequest(
            request_id=str(uuid.uuid4()),
            source_service=SERVICE_NAME,
            target_service=target_service,
            function_name=function_path,
            args=list(args),
            kwargs=kwargs,
            timestamp=time.time()
        )
        
        future = Future()
        self._pending_requests[request.request_id] = future
        
        self._producer.send(RPC_TOPIC, request.to_json())
        self._producer.flush()
        
        return future
    
    def shutdown(self):
        """Shutdown the RPC client."""
        self._running = False
        if self._producer:
            self._producer.close()
        if self._executor:
            self._executor.shutdown(wait=False)


class RPCServer:
    """
    Server that listens for and executes incoming RPC requests.
    """
    _instance = None
    _consumer = None
    _producer = None
    _running: bool = False
    _thread: threading.Thread = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._running = False
        return cls._instance
    
    def start(self):
        """Start the RPC server in a background thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"[Qyro RPC] Server started for service: {SERVICE_NAME}")
    
    def _run(self):
        """Main server loop."""
        try:
            from kafka import KafkaConsumer, KafkaProducer
            
            self._consumer = KafkaConsumer(
                RPC_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=f"qyro-rpc-server-{SERVICE_NAME}",
                auto_offset_reset='latest',
                value_deserializer=lambda x: x.decode('utf-8'),
                consumer_timeout_ms=1000
            )
            
            self._producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: v.encode('utf-8'),
                acks='all'
            )
            
            while self._running:
                try:
                    for message in self._consumer:
                        self._handle_request(message.value)
                except Exception as e:
                    if self._running:
                        time.sleep(0.1)
                        
        except Exception as e:
            print(f"[Qyro RPC] Server error: {e}")
    
    def _handle_request(self, message: str):
        """Handle an incoming RPC request."""
        try:
            request = RPCRequest.from_json(message)
            
            # Check if this request is for us
            if request.target_service != SERVICE_NAME:
                return
            
            # Execute the function
            try:
                result = registry.execute(
                    request.function_name,
                    request.args,
                    request.kwargs
                )
                
                response = RPCResponse(
                    request_id=request.request_id,
                    source_service=SERVICE_NAME,
                    success=True,
                    result=result,
                    error=None,
                    timestamp=time.time()
                )
                
            except Exception as e:
                response = RPCResponse(
                    request_id=request.request_id,
                    source_service=SERVICE_NAME,
                    success=False,
                    result=None,
                    error=str(e),
                    timestamp=time.time()
                )
            
            # Send response
            self._producer.send(RPC_RESPONSE_TOPIC, response.to_json())
            self._producer.flush()
            
        except Exception as e:
            print(f"[Qyro RPC] Error handling request: {e}")
    
    def stop(self):
        """Stop the RPC server."""
        self._running = False
        if self._consumer:
            self._consumer.close()
        if self._producer:
            self._producer.close()


# Global instances
_client = RPCClient()
_server = RPCServer()


def call(function_path: str, *args, timeout: float = None, **kwargs) -> Any:
    """
    Call a function in another service.
    
    Example:
        result = call("api.calculate", 1, 2)
        result = call("java-service.process_order", order_id=123)
    """
    return _client.call(function_path, *args, timeout=timeout, **kwargs)


def call_async(function_path: str, *args, **kwargs) -> Future:
    """
    Call a function asynchronously, returns a Future.
    
    Example:
        future = call_async("api.slow_operation", data)
        # ... do other work ...
        result = future.result(timeout=10)
    """
    return _client.call_async(function_path, *args, **kwargs)


def start_server():
    """Start the RPC server to handle incoming calls."""
    _server.start()


def list_exposed_functions() -> List[Dict[str, Any]]:
    """List all functions exposed by this service."""
    return registry.list_functions()


# Auto-start server when module is imported in a service context
if SERVICE_NAME != "unknown":
    start_server()
