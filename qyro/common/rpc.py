"""
Nexus Cross-Language Function Calling System (Redis-Backed)
Enables any language to call functions registered in any other language.

Re-architected for Phase 0 Core Repair to use Redis Lists/PubSub.
"""

import json
import time
import uuid
import threading
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field, asdict
from enum import IntEnum
from functools import wraps

from .logging import get_logger

logger = get_logger("nexus.rpc")

class CallStatus(IntEnum):
    PENDING = 0
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3
    TIMEOUT = 4

@dataclass
class FunctionInfo:
    name: str
    language: str
    process_id: str
    param_types: List[str] = field(default_factory=list)
    return_type: str = "any"
    
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**d)

@dataclass
class FunctionCall:
    call_id: str
    function_name: str
    args: List[Any]
    kwargs: Dict[str, Any]
    caller_id: str
    timestamp: float
    status: CallStatus = CallStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    
    def to_dict(self):
        d = asdict(self)
        d['status'] = int(self.status)
        return d
    
    @classmethod
    def from_dict(cls, d):
        d['status'] = CallStatus(d.get('status', 0))
        return cls(**d)

class NexusRPC:
    """
    Redis-backed RPC System.
    Uses Redis Lists for Task Queue and Pub/Sub for Results.
    """

    # Redis Keys
    KEY_REGISTRY = "nexus:rpc:registry"
    KEY_QUEUE = "nexus:rpc:queue"
    KEY_RESULT_PREFIX = "nexus:rpc:result:"
    KEY_BROKER_LOCK = "nexus:rpc:broker_lock"
    
    def __init__(self, memory, mode: str = "event"):
        self._memory = memory  # Expects RedisNexusMemory
        self._mode = mode
        self._local_handlers: Dict[str, Callable] = {}
        self._process_id = str(uuid.uuid4())[:8]
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        # Ensure we have a Redis client
        if not hasattr(memory, '_redis'):
             logger.warning("rpc_compatibility_mode", msg="Falling back to legacy memory (not supported)")
             self._redis = None
        else:
             self._redis = memory._redis

    def register(self, name: str, handler: Callable, **kwargs):
        """Register a function."""
        self._local_handlers[name] = handler
        
        info = FunctionInfo(
            name=name,
            language="python",
            process_id=self._process_id,
            param_types=kwargs.get('param_types', []),
            return_type=kwargs.get('return_type', 'any')
        )
        
        if self._redis:
            self._redis.hset(self.KEY_REGISTRY, name, json.dumps(info.to_dict()))
        
        logger.info("rpc_registered", name=name)

    def unregister(self, name: str):
        if name in self._local_handlers:
            del self._local_handlers[name]
        if self._redis:
            self._redis.hdel(self.KEY_REGISTRY, name)

    def export(self, name: str = None, **kwargs):
        """Decorator to export function."""
        def decorator(func: Callable):
            fn_name = name or func.__name__
            self.register(fn_name, func, **kwargs)
            
            @wraps(func)
            def wrapper(*args, **kw):
                return func(*args, **kw)
            return wrapper
        return decorator

    def call(self, function_name: str, *args, timeout: float = 10.0, **kwargs) -> Any:
        """Execute a remote function call."""
        if not self._redis:
            raise RuntimeError("RPC requires Redis connection")

        # 1. Look up function owner
        raw_info = self._redis.hget(self.KEY_REGISTRY, function_name)
        if not raw_info:
            raise ValueError(f"Function not found in registry: {function_name}")

        info = json.loads(raw_info)
        target_pid = info.get('process_id')

        if not target_pid:
             raise ValueError(f"Function {function_name} has no owner (僵尸 state?)")

        call_id = str(uuid.uuid4())
        call = FunctionCall(
            call_id=call_id,
            function_name=function_name,
            args=list(args),
            kwargs=kwargs,
            caller_id=self._process_id,
            timestamp=time.time()
        )

        # 2. Push to TARGET Queue (O(1) routing)
        target_queue = f"{self.KEY_QUEUE}:{target_pid}"
        self._redis.rpush(target_queue, json.dumps(call.to_dict()))

        # 3. Use Pub/Sub for result instead of polling
        result_channel = f"{self.KEY_RESULT_PREFIX}{call_id}"

        # Create a pubsub connection to listen for the result
        pubsub = self._redis.pubsub()
        pubsub.subscribe(result_channel)

        # 4. Wait for Result via Pub/Sub with proper timeout handling
        start = time.time()
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        res = FunctionCall.from_dict(json.loads(message['data']))

                        if res.status == CallStatus.FAILED:
                            raise RuntimeError(res.error)
                        return res.result
                    except json.JSONDecodeError as e:
                        logger.error("rpc_result_parse_error", call_id=call_id, error=str(e))
                        continue
                    except Exception as e:
                        logger.error("rpc_result_processing_error", call_id=call_id, error=str(e))
                        raise

                # Check for timeout
                if time.time() - start >= timeout:
                    raise TimeoutError(f"RPC Timeout: {function_name} after {timeout}s")

        except Exception as e:
            # Clean up the result key if there's an error
            try:
                self._redis.delete(f"{self.KEY_RESULT_PREFIX}{call_id}")
            except:
                pass
            raise
        finally:
            try:
                pubsub.close()
            except:
                pass

    def start_handler(self):
        """Start the worker thread."""
        if self._running: return
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("rpc_worker_started", pid=self._process_id)

    def stop_handler(self):
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=1.0)

    def _worker_loop(self):
        """Continuously process calls from MY queue."""
        my_queue = f"{self.KEY_QUEUE}:{self._process_id}"

        while self._running:
            try:
                if not self._redis:
                    time.sleep(1)
                    continue

                # BLPOP from MY dedicated queue with proper error handling
                try:
                    item = self._redis.blpop(my_queue, timeout=1)
                    if not item:
                        continue

                    _, data = item
                    call = FunctionCall.from_dict(json.loads(data))

                    # Execute (No need to check ownership, if it's in my queue, it's for me)
                    self._execute_call(call)

                except Exception as blpop_error:
                    logger.error("rpc_blpop_error", error=str(blpop_error))
                    # Brief pause before continuing to avoid tight loop on connection errors
                    time.sleep(0.1)
                    continue

            except Exception as e:
                logger.error("rpc_worker_error", error=str(e))
                time.sleep(1)

    def _execute_call(self, call: FunctionCall):
        """Execute a function call and publish the result."""
        try:
            if call.function_name in self._local_handlers:
                handler = self._local_handlers[call.function_name]

                # Update call status to processing
                call.status = CallStatus.PROCESSING

                # Execute the handler
                result = handler(*call.args, **call.kwargs)

                # Update call with result
                call.status = CallStatus.COMPLETED
                call.result = result
            else:
                # Function not found in this process
                call.status = CallStatus.FAILED
                call.error = f"Function '{call.function_name}' not found in this module"
                logger.error("rpc_function_not_found", function_name=call.function_name)

        except Exception as e:
            call.status = CallStatus.FAILED
            call.error = str(e)
            logger.error("rpc_execution_failed", fn=call.function_name, error=str(e))

        # Publish result via Pub/Sub instead of storing in key
        result_channel = f"{self.KEY_RESULT_PREFIX}{call.call_id}"

        # Use Redis pipeline for atomic operation
        with self._redis.pipeline() as pipe:
            pipe.publish(result_channel, json.dumps(call.to_dict()))
            # Set expiration for the result channel to prevent accumulation
            pipe.expire(result_channel, 300)  # 5 minutes
            pipe.execute()

        logger.debug("rpc_call_executed", call_id=call.call_id, status=call.status.name)



# Dummy Registry class for backwards compatibility imports if needed
class FunctionRegistry:
    def __init__(self, *args): pass

def nexus_export(name=None, **kwargs):
    def dec(f): return f
    return dec
