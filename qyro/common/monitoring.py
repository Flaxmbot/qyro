"""
Qyro Monitoring and Observability System
Production-grade metrics, health checks, and observability for the Qyro runtime.
"""

import time
import threading
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import psutil
import os
import logging
from collections import deque
from contextlib import contextmanager


class Severity(Enum):
    """Log severity levels."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@dataclass
class LogEntry:
    """A single log entry."""
    timestamp: float
    level: Severity
    message: str
    module: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricPoint:
    """A single metric measurement."""
    name: str
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and stores metrics for the Qyro system."""
    
    def __init__(self, retention_minutes: int = 60):
        self.retention_seconds = retention_minutes * 60
        self.metrics: Dict[str, deque] = {}
        self._lock = threading.Lock()
        self.start_time = time.time()
        
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a metric value."""
        labels = labels or {}
        key = f"{name}:{json.dumps(labels, sort_keys=True)}"
        
        with self._lock:
            if key not in self.metrics:
                self.metrics[key] = deque()
            
            # Remove old metrics beyond retention period
            now = time.time()
            while self.metrics[key] and (now - self.metrics[key][0].timestamp) > self.retention_seconds:
                self.metrics[key].popleft()
            
            metric_point = MetricPoint(
                name=name,
                value=value,
                timestamp=now,
                labels=labels
            )
            self.metrics[key].append(metric_point)
    
    def get_latest(self, name: str, labels: Dict[str, str] = None) -> Optional[MetricPoint]:
        """Get the latest value for a metric."""
        labels = labels or {}
        key = f"{name}:{json.dumps(labels, sort_keys=True)}"
        
        with self._lock:
            if key in self.metrics and self.metrics[key]:
                return self.metrics[key][-1]
            return None
    
    def get_values(self, name: str, labels: Dict[str, str] = None, 
                   since: float = None) -> List[MetricPoint]:
        """Get metric values, optionally filtered by time."""
        labels = labels or {}
        key = f"{name}:{json.dumps(labels, sort_keys=True)}"
        
        with self._lock:
            if key not in self.metrics:
                return []
            
            values = list(self.metrics[key])
            if since is not None:
                values = [v for v in values if v.timestamp >= since]
            
            return values
    
    def get_system_metrics(self) -> Dict[str, float]:
        """Get system-level metrics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'process_count': len(psutil.pids()),
            'uptime_seconds': time.time() - self.start_time
        }


class Logger:
    """Production-grade logger with structured logging."""
    
    def __init__(self, name: str = "qyro", level: Severity = Severity.INFO):
        self.name = name
        self.level = level
        self.handlers: List[Callable[[LogEntry], None]] = []
        self._lock = threading.Lock()
        
        # Add default console handler
        self.add_handler(self._console_handler)
    
    def add_handler(self, handler: Callable[[LogEntry], None]):
        """Add a log handler."""
        with self._lock:
            self.handlers.append(handler)
    
    def _console_handler(self, entry: LogEntry):
        """Default console handler."""
        timestamp = datetime.fromtimestamp(entry.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        level_name = entry.level.name
        print(f"[{timestamp}] [{level_name}] [{entry.module}] {entry.message}")
        if entry.details:
            print(f"  Details: {entry.details}")
    
    def _log(self, level: Severity, message: str, module: str = "", **details):
        """Internal logging method."""
        if level.value < self.level.value:
            return
        
        entry = LogEntry(
            timestamp=time.time(),
            level=level,
            message=message,
            module=module or self.name,
            details=details
        )
        
        with self._lock:
            for handler in self.handlers:
                try:
                    handler(entry)
                except Exception:
                    # Never let logging errors break the application
                    pass
    
    def debug(self, message: str, module: str = "", **details):
        self._log(Severity.DEBUG, message, module, **details)
    
    def info(self, message: str, module: str = "", **details):
        self._log(Severity.INFO, message, module, **details)
    
    def warning(self, message: str, module: str = "", **details):
        self._log(Severity.WARNING, message, module, **details)
    
    def error(self, message: str, module: str = "", **details):
        self._log(Severity.ERROR, message, module, **details)
    
    def critical(self, message: str, module: str = "", **details):
        self._log(Severity.CRITICAL, message, module, **details)


class HealthChecker:
    """Health checking system for the Qyro runtime."""
    
    def __init__(self, metrics_collector: MetricsCollector, logger: Logger):
        self.metrics = metrics_collector
        self.logger = logger
        self.checks: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self._lock = threading.Lock()
    
    def register_check(self, name: str, check_func: Callable[[], Dict[str, Any]]):
        """Register a health check function."""
        with self._lock:
            self.checks[name] = check_func
    
    def run_checks(self) -> Dict[str, Dict[str, Any]]:
        """Run all registered health checks."""
        results = {}
        
        for name, check_func in self.checks.items():
            try:
                result = check_func()
                results[name] = result
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': time.time()
                }
        
        return results
    
    def get_health_status(self) -> str:
        """Get overall health status."""
        results = self.run_checks()
        
        # If any check failed, return unhealthy
        for result in results.values():
            if result.get('status') == 'error' or result.get('healthy') is False:
                return 'unhealthy'
        
        return 'healthy'


class QyroMonitor:
    """Main monitoring system for Qyro runtime."""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.logger = Logger()
        self.health = HealthChecker(self.metrics, self.logger)
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        
        # Register default health checks
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks."""
        def check_system_resources():
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            healthy = cpu_percent < 90 and memory_percent < 90 and disk_percent < 90
            
            return {
                'status': 'healthy' if healthy else 'degraded',
                'healthy': healthy,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'timestamp': time.time()
            }
        
        def check_process_count():
            proc_count = len(psutil.pids())
            healthy = proc_count < 1000  # Arbitrary limit
            
            return {
                'status': 'healthy' if healthy else 'warning',
                'healthy': healthy,
                'process_count': proc_count,
                'timestamp': time.time()
            }
        
        self.health.register_check('system_resources', check_system_resources)
        self.health.register_check('process_count', check_process_count)
    
    def start_monitoring(self, interval: float = 30.0):
        """Start background monitoring."""
        if self._running:
            return
        
        self._running = True
        
        def monitor_loop():
            while not self._stop_event.is_set():
                try:
                    # Collect system metrics
                    sys_metrics = self.metrics.get_system_metrics()
                    for name, value in sys_metrics.items():
                        self.metrics.record_metric(f"system.{name}", value)
                    
                    # Run health checks
                    health_results = self.health.run_checks()
                    
                    # Log health status
                    overall_status = self.health.get_health_status()
                    self.logger.info(f"Health check completed - Overall: {overall_status}", 
                                   module="monitor", health_results=health_results)
                    
                    # Wait for next interval or stop event
                    if self._stop_event.wait(timeout=interval):
                        break
                        
                except Exception as e:
                    self.logger.error(f"Monitoring error: {e}", module="monitor")
                    # Wait a bit before retrying
                    if self._stop_event.wait(timeout=5.0):
                        break
        
        self._monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5.0)  # Wait up to 5 seconds
        
        self._stop_event.clear()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics."""
        return {
            'system': self.metrics.get_system_metrics(),
            'health_status': self.health.get_health_status(),
            'health_details': self.health.run_checks(),
            'uptime': time.time() - self.metrics.start_time
        }
    
    def record_custom_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a custom metric."""
        self.metrics.record_metric(name, value, labels)
    
    def log_event(self, level: Severity, message: str, module: str = "", **details):
        """Log an event."""
        if level == Severity.DEBUG:
            self.logger.debug(message, module, **details)
        elif level == Severity.INFO:
            self.logger.info(message, module, **details)
        elif level == Severity.WARNING:
            self.logger.warning(message, module, **details)
        elif level == Severity.ERROR:
            self.logger.error(message, module, **details)
        elif level == Severity.CRITICAL:
            self.logger.critical(message, module, **details)


# Global monitor instance
_qyro_monitor: Optional[QyroMonitor] = None


def get_monitor() -> QyroMonitor:
    """Get the global monitor instance."""
    global _qyro_monitor
    if _qyro_monitor is None:
        _qyro_monitor = QyroMonitor()
    return _qyro_monitor


def start_monitoring(interval: float = 30.0):
    """Start the monitoring system."""
    monitor = get_monitor()
    monitor.start_monitoring(interval)


def stop_monitoring():
    """Stop the monitoring system."""
    monitor = get_monitor()
    monitor.stop_monitoring()


@contextmanager
def monitor_performance(metric_name: str, labels: Dict[str, str] = None):
    """Context manager to monitor performance of a code block."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        monitor = get_monitor()
        monitor.record_custom_metric(metric_name, duration, labels)


# Example usage and health check endpoints for integration
def create_health_endpoints(app):
    """Add health check endpoints to a web application (FastAPI/Flask)."""
    monitor = get_monitor()
    
    try:
        # Try FastAPI
        from fastapi import APIRouter
        router = APIRouter()
        
        @router.get("/health")
        def health_check():
            return {
                "status": monitor.health.get_health_status(),
                "checks": monitor.health.run_checks(),
                "timestamp": time.time()
            }
        
        @router.get("/metrics")
        def metrics_endpoint():
            return monitor.get_metrics_summary()
        
        @router.get("/live")
        def liveness():
            # Liveness probe - just check if the service is running
            return {"status": "alive", "timestamp": time.time()}
        
        @router.get("/ready")
        def readiness():
            # Readiness probe - check if the service is ready to serve requests
            health_status = monitor.health.get_health_status()
            return {
                "status": "ready" if health_status == "healthy" else "not_ready",
                "health": health_status,
                "timestamp": time.time()
            }
        
        app.include_router(router)
        return router
        
    except ImportError:
        pass
    
    try:
        # Try Flask
        from flask import jsonify
        
        @app.route("/health")
        def health_check():
            return jsonify({
                "status": monitor.health.get_health_status(),
                "checks": monitor.health.run_checks(),
                "timestamp": time.time()
            })
        
        @app.route("/metrics")
        def metrics_endpoint():
            return jsonify(monitor.get_metrics_summary())
        
        @app.route("/live")
        def liveness():
            return jsonify({"status": "alive", "timestamp": time.time()})
        
        @app.route("/ready")
        def readiness():
            health_status = monitor.health.get_health_status()
            return jsonify({
                "status": "ready" if health_status == "healthy" else "not_ready",
                "health": health_status,
                "timestamp": time.time()
            })
            
    except ImportError:
        pass


# Initialize monitoring when module is loaded
def _init_monitoring():
    """Initialize monitoring system."""
    monitor = get_monitor()
    
    # Start monitoring in background
    monitor.start_monitoring()
    
    # Log system startup
    monitor.log_event(Severity.INFO, "Qyro monitoring system initialized", "monitor")


# Initialize monitoring
_init_monitoring()