"""
Qyro Memory Compatibility Layer
Provides backward compatibility with older QyroMemory API.
Supports Redis, distributed Redis, and standalone in-memory implementations.
"""

import os
import socket
from typing import Optional, Dict, Any, Callable, List

from .redis_memory import RedisQyroMemory, RedisConnectionError as MemoryConnectionError
# from .distributed_memory import create_distributed_memory  # Commented out as file was removed
# from .standalone_memory import StandaloneNexusMemory  # Commented out as file was removed

class NexusMemory:
    """
    Backward-compatible wrapper supporting Redis, distributed, and standalone implementations.

    This class provides the old QyroMemory API interface while
    automatically selecting the appropriate backend based on availability.
    """

    def __init__(self, create: bool = True, redis_host: str = 'localhost', redis_port: int = 6379,
                 use_distributed: bool = False, cluster_hosts: list = None, cluster_ports: list = None,
                 force_standalone: bool = None):
        """
        Initialize QyroMemory with Redis, distributed, or standalone backend.

        Args:
            create: Unused (kept for backward compatibility)
            redis_host: Redis server hostname (for single Redis mode)
            redis_port: Redis server port (for single Redis mode)
            use_distributed: Whether to use distributed memory system
            cluster_hosts: List of Redis hosts for distributed mode
            cluster_ports: List of Redis ports for distributed mode
            force_standalone: Force standalone mode (True), Redis mode (False), or auto-detect (None)
        """
        # Check if standalone mode is forced via parameter or environment
        if force_standalone is None:
            force_standalone = os.environ.get('QYRO_STANDALONE_MODE', '').lower() == 'true'

        if force_standalone:
            # Use standalone memory regardless of Redis availability - functionality removed in this version
            print("[QYRO] Standalone mode requested but not available, using Redis]")
            # Fall through to Redis mode
            force_standalone = False
        elif use_distributed:
            # Use distributed memory system - functionality removed in this version
            print(f"[QYRO] Distributed memory requested but not available, using Redis")
            # Fall through to Redis mode
            use_distributed = False
        else:
            # Try Redis first, fallback to standalone
            try:
                # Check if Redis is available before connecting
                if self._is_redis_available(redis_host, redis_port):
                    self._memory = RedisQyroMemory(host=redis_host, port=redis_port)
                    self._backend_type = 'redis'
                    print(f"[QYRO] Connected to Redis at {redis_host}:{redis_port}")
                else:
                    print(f"[QYRO] Redis not available at {redis_host}:{redis_port}, exiting")
                    raise RuntimeError(f"Redis not available at {redis_host}:{redis_port} and standalone mode not available")
            except Exception as e:
                print(f"[QYRO] Redis connection failed: {e}, exiting")
                raise RuntimeError(f"Redis connection failed: {e} and standalone mode not available")

        self._redis_host = redis_host
        self._redis_port = redis_port
        self._use_distributed = use_distributed

    def _is_redis_available(self, host: str, port: int) -> bool:
        """Check if Redis is available without creating a full connection."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 second timeout
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    def read(self) -> dict:
        """
        Read the current state from Redis.

        Returns:
            Dictionary containing the current state.
        """
        if self._use_distributed:
            return self._memory.read('state')  # Distributed memory uses keys
        else:
            return self._memory.read()

    def write(self, data: dict) -> None:
        """
        Write state to Redis.

        Args:
            data: Dictionary containing state to write
        """
        if self._use_distributed:
            self._memory.write('state', data)  # Distributed memory uses keys
        else:
            self._memory.write(data)

    def subscribe_to_changes(self, callback) -> None:
        """
        Subscribe to state change notifications.

        Args:
            callback: Function to call when state changes
        """
        if self._use_distributed:
            self._memory.subscribe_to_topic('qyro:state:changed', callback)
        else:
            self._memory.subscribe_to_changes(callback)

    def close(self) -> None:
        """Close Redis connections."""
        self._memory.close()

    def clear(self) -> None:
        """Clear all state."""
        if self._use_distributed:
            # In distributed mode, we might want to clear from all shards
            # For now, just clear from the 'state' key in the appropriate shard
            self._memory.write('state', {})
        else:
            self._memory.clear_state()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


# Export aliases for backward compatibility
NexusConnectionError = MemoryConnectionError

# Qyro compatibility alias
class QyroMemory(NexusMemory):
    """Qyro memory class for backward compatibility."""
    pass
