"""
Qyro Configuration Module
Handles configuration management for the Qyro runtime.
"""

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class QyroConfig:
    """Configuration for Qyro runtime."""
    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Kafka configuration
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_prefix: str = "Qyro_"
    
    # Service configuration
    service_host: str = "0.0.0.0"
    service_port: int = 8765
    
    # Debugging
    debug: bool = False
    
    # Resource limits
    max_memory_mb: int = 512
    max_cpu_percent: int = 80
    
    # Process management
    max_restarts: int = 5
    restart_backoff: float = 2.0
    
    def __post_init__(self):
        """Load configuration from environment variables if not provided."""
        # Redis configuration
        if self.redis_host == "localhost":
            self.redis_host = os.getenv("REDIS_HOST", "localhost")
        if self.redis_port == 6379:
            self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        if self.redis_password is None:
            self.redis_password = os.getenv("REDIS_PASSWORD")
        
        # Kafka configuration
        if self.kafka_bootstrap_servers == "localhost:9092":
            self.kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        if self.kafka_topic_prefix == "Qyro_":
            self.kafka_topic_prefix = os.getenv("KAFKA_TOPIC_PREFIX", "Qyro_")
        
        # Service configuration
        if self.service_host == "0.0.0.0":
            self.service_host = os.getenv("SERVICE_HOST", "0.0.0.0")
        if self.service_port == 8765:
            self.service_port = int(os.getenv("SERVICE_PORT", "8765"))
        
        # Debug configuration
        if not self.debug:
            self.debug = os.getenv("DEBUG", "").lower() == "true"
        
        # Resource limits
        if self.max_memory_mb == 512:
            self.max_memory_mb = int(os.getenv("MAX_MEMORY_MB", "512"))
        if self.max_cpu_percent == 80:
            self.max_cpu_percent = int(os.getenv("MAX_CPU_PERCENT", "80"))
        
        # Process management
        if self.max_restarts == 5:
            self.max_restarts = int(os.getenv("MAX_RESTARTS", "5"))
        if self.restart_backoff == 2.0:
            self.restart_backoff = float(os.getenv("RESTART_BACKOFF", "2.0"))

    @property
    def redis_url(self) -> str:
        """Get Redis URL for connection."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def kafka_topics(self) -> dict:
        """Get Kafka topic names."""
        return {
            "state_change": f"{self.kafka_topic_prefix}state_change",
            "module_events": f"{self.kafka_topic_prefix}module_events",
            "rpc_requests": f"{self.kafka_topic_prefix}rpc_requests",
            "rpc_responses": f"{self.kafka_topic_prefix}rpc_responses",
            "broadcast": f"{self.kafka_topic_prefix}broadcast"
        }
