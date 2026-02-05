"""
Nexus Health Check System
Provides health check endpoints and metrics for monitoring.
"""

import time
import os
import psutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .logging import get_logger
from .constants import PROTOCOL_VERSION, MEM_FILE

logger = get_logger("nexus.health")


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a single component."""
    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """Overall system health status."""
    status: HealthStatus
    version: str
    uptime_seconds: float
    components: List[ComponentHealth]
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "version": self.version,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "timestamp": self.timestamp,
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "latency_ms": round(c.latency_ms, 2),
                    "metadata": c.metadata
                }
                for c in self.components
            ]
        }


class HealthChecker:
    """
    Health check system for Nexus runtime.
    
    Checks:
    - Memory availability and integrity
    - Lock file accessibility
    - Process status
    - Resource usage
    """
    
    def __init__(self, memory=None, orchestrator=None):
        self._memory = memory
        self._orchestrator = orchestrator
        self._start_time = time.time()
        self._version = f"2.0.0-nbp{PROTOCOL_VERSION}"
    
    def check(self) -> SystemHealth:
        """Perform full health check."""
        components = []
        
        # Check memory
        components.append(self._check_memory())
        
        # Check lock file
        components.append(self._check_lock())
        
        # Check processes
        if self._orchestrator:
            components.append(self._check_processes())
        
        # Check system resources
        components.append(self._check_resources())
        
        # Determine overall status
        statuses = [c.status for c in components]
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.UNHEALTHY
        else:
            overall = HealthStatus.DEGRADED
        
        return SystemHealth(
            status=overall,
            version=self._version,
            uptime_seconds=time.time() - self._start_time,
            components=components
        )
    
    def _check_memory(self) -> ComponentHealth:
        """Check shared memory health."""
        start = time.time()
        
        try:
            if not os.path.exists(MEM_FILE):
                return ComponentHealth(
                    name="memory",
                    status=HealthStatus.UNHEALTHY,
                    message="Memory file not found"
                )
            
            # Check file size
            size = os.path.getsize(MEM_FILE)
            if size < 1000:
                return ComponentHealth(
                    name="memory",
                    status=HealthStatus.DEGRADED,
                    message=f"Memory file too small: {size} bytes"
                )
            
            # Try to read if memory object available
            if self._memory:
                try:
                    stats = self._memory.get_stats()
                    latency = (time.time() - start) * 1000
                    
                    return ComponentHealth(
                        name="memory",
                        status=HealthStatus.HEALTHY,
                        message="Memory accessible",
                        latency_ms=latency,
                        metadata={
                            "size_mb": round(stats.get("total_size", 0) / 1024 / 1024, 2),
                            "utilization": round(stats.get("utilization", 0) * 100, 1),
                            "sequence": stats.get("sequence", 0),
                            "encrypted": stats.get("encrypted", False),
                            "protocol": stats.get("protocol_version", 0)
                        }
                    )
                except Exception as e:
                    return ComponentHealth(
                        name="memory",
                        status=HealthStatus.DEGRADED,
                        message=f"Memory read error: {str(e)}"
                    )
            
            return ComponentHealth(
                name="memory",
                status=HealthStatus.HEALTHY,
                message=f"Memory file exists ({size} bytes)",
                latency_ms=(time.time() - start) * 1000
            )
            
        except Exception as e:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNHEALTHY,
                message=str(e)
            )
    
    def _check_lock(self) -> ComponentHealth:
        """Check lock file accessibility."""
        lock_file = ".nexus_global.lock"
        start = time.time()
        
        try:
            # Try to open lock file
            with open(lock_file, 'a') as f:
                pass
            
            return ComponentHealth(
                name="lock",
                status=HealthStatus.HEALTHY,
                message="Lock file accessible",
                latency_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ComponentHealth(
                name="lock",
                status=HealthStatus.DEGRADED,
                message=f"Lock file issue: {str(e)}"
            )
    
    def _check_processes(self) -> ComponentHealth:
        """Check supervised process health."""
        try:
            if not self._orchestrator:
                return ComponentHealth(
                    name="processes",
                    status=HealthStatus.UNKNOWN,
                    message="No orchestrator"
                )
            
            status = self._orchestrator.get_status()
            processes = status.get("processes", [])
            
            running = sum(1 for p in processes if p.get("status") == "running")
            total = len(processes)
            
            if running == total:
                return ComponentHealth(
                    name="processes",
                    status=HealthStatus.HEALTHY,
                    message=f"All {total} processes running",
                    metadata={"running": running, "total": total}
                )
            elif running > 0:
                return ComponentHealth(
                    name="processes",
                    status=HealthStatus.DEGRADED,
                    message=f"{running}/{total} processes running",
                    metadata={"running": running, "total": total}
                )
            else:
                return ComponentHealth(
                    name="processes",
                    status=HealthStatus.UNHEALTHY,
                    message="No processes running",
                    metadata={"running": 0, "total": total}
                )
                
        except Exception as e:
            return ComponentHealth(
                name="processes",
                status=HealthStatus.UNKNOWN,
                message=str(e)
            )
    
    def _check_resources(self) -> ComponentHealth:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            # Determine status based on usage
            if memory.percent > 90 or disk.percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "Critical resource usage"
            elif memory.percent > 75 or disk.percent > 80:
                status = HealthStatus.DEGRADED
                message = "High resource usage"
            else:
                status = HealthStatus.HEALTHY
                message = "Resources OK"
            
            return ComponentHealth(
                name="resources",
                status=status,
                message=message,
                metadata={
                    "cpu_percent": round(cpu_percent, 1),
                    "memory_percent": round(memory.percent, 1),
                    "memory_available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                    "disk_percent": round(disk.percent, 1),
                    "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="resources",
                status=HealthStatus.UNKNOWN,
                message=str(e)
            )
    
    def liveness(self) -> bool:
        """Simple liveness check (is the process alive)."""
        return True
    
    def readiness(self) -> bool:
        """
        Readiness check (is the service ready to handle requests).
        Returns True if memory is accessible.
        """
        try:
            return os.path.exists(MEM_FILE)
        except:
            return False


# HTTP Health Endpoint Handler (for FastAPI/Flask integration)
def create_health_routes(app, health_checker: HealthChecker):
    """
    Add health check routes to a FastAPI or Flask app.
    
    Usage (FastAPI):
        from nexus_core.health import HealthChecker, create_health_routes
        health = HealthChecker(memory)
        create_health_routes(app, health)
    """
    try:
        # Try FastAPI
        from fastapi import APIRouter
        router = APIRouter()
        
        @router.get("/health")
        def health():
            return health_checker.check().to_dict()
        
        @router.get("/health/live")
        def liveness():
            return {"status": "alive" if health_checker.liveness() else "dead"}
        
        @router.get("/health/ready")
        def readiness():
            return {"status": "ready" if health_checker.readiness() else "not_ready"}
        
        app.include_router(router)
        return router
        
    except ImportError:
        pass
    
    try:
        # Try Flask
        from flask import jsonify
        
        @app.route("/health")
        def health():
            return jsonify(health_checker.check().to_dict())
        
        @app.route("/health/live")
        def liveness():
            return jsonify({"status": "alive" if health_checker.liveness() else "dead"})
        
        @app.route("/health/ready")
        def readiness():
            return jsonify({"status": "ready" if health_checker.readiness() else "not_ready"})
            
    except ImportError:
        logger.warning("no_web_framework", msg="Neither FastAPI nor Flask found")


# Global health checker instance
_health_checker: Optional[HealthChecker] = None

def get_health_checker(memory=None, orchestrator=None) -> HealthChecker:
    """Get or create the global health checker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker(memory, orchestrator)
    return _health_checker
