"""
Nexus Metrics Collection
Prometheus-compatible metrics for observability.
"""

import time
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from contextlib import contextmanager

from .logging import get_logger

logger = get_logger("nexus.metrics")


@dataclass
class MetricValue:
    """A single metric value with labels."""
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class Counter:
    """A counter metric that only increases."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._values: Dict[tuple, float] = {}
        self._lock = threading.Lock()
    
    def inc(self, amount: float = 1.0, **labels):
        """Increment the counter."""
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[key] = self._values.get(key, 0) + amount
    
    def get(self, **labels) -> float:
        """Get current value."""
        key = tuple(sorted(labels.items()))
        return self._values.get(key, 0)
    
    def values(self) -> List[MetricValue]:
        """Get all values with labels."""
        result = []
        for key, value in self._values.items():
            labels = dict(key)
            result.append(MetricValue(value=value, labels=labels))
        return result


class Gauge:
    """A gauge metric that can go up and down."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._values: Dict[tuple, float] = {}
        self._lock = threading.Lock()
    
    def set(self, value: float, **labels):
        """Set the gauge value."""
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[key] = value
    
    def inc(self, amount: float = 1.0, **labels):
        """Increment the gauge."""
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[key] = self._values.get(key, 0) + amount
    
    def dec(self, amount: float = 1.0, **labels):
        """Decrement the gauge."""
        self.inc(-amount, **labels)
    
    def get(self, **labels) -> float:
        """Get current value."""
        key = tuple(sorted(labels.items()))
        return self._values.get(key, 0)
    
    def values(self) -> List[MetricValue]:
        """Get all values with labels."""
        result = []
        for key, value in self._values.items():
            labels = dict(key)
            result.append(MetricValue(value=value, labels=labels))
        return result


class Histogram:
    """A histogram metric for measuring distributions."""
    
    DEFAULT_BUCKETS = (0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    
    def __init__(self, name: str, description: str = "", buckets: tuple = None):
        self.name = name
        self.description = description
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._counts: Dict[tuple, Dict[float, int]] = {}
        self._sums: Dict[tuple, float] = {}
        self._totals: Dict[tuple, int] = {}
        self._lock = threading.Lock()
    
    def observe(self, value: float, **labels):
        """Record an observation."""
        key = tuple(sorted(labels.items()))
        
        with self._lock:
            if key not in self._counts:
                self._counts[key] = {b: 0 for b in self.buckets}
                self._counts[key][float('inf')] = 0
                self._sums[key] = 0
                self._totals[key] = 0
            
            for bucket in self.buckets:
                if value <= bucket:
                    self._counts[key][bucket] += 1
            self._counts[key][float('inf')] += 1
            
            self._sums[key] += value
            self._totals[key] += 1
    
    @contextmanager
    def time(self, **labels):
        """Context manager to measure duration."""
        start = time.time()
        yield
        self.observe(time.time() - start, **labels)
    
    def get_percentile(self, percentile: float, **labels) -> float:
        """Estimate a percentile from the histogram."""
        key = tuple(sorted(labels.items()))
        if key not in self._totals or self._totals[key] == 0:
            return 0.0
        
        target = self._totals[key] * percentile / 100
        cumulative = 0
        prev_bucket = 0
        
        for bucket in sorted(self.buckets):
            cumulative = self._counts[key].get(bucket, 0)
            if cumulative >= target:
                return bucket
            prev_bucket = bucket
        
        return self.buckets[-1]


class MetricsRegistry:
    """Registry of all metrics."""
    
    def __init__(self, prefix: str = "nexus"):
        self.prefix = prefix
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
    
    def counter(self, name: str, description: str = "") -> Counter:
        """Get or create a counter."""
        full_name = f"{self.prefix}_{name}"
        if full_name not in self._counters:
            self._counters[full_name] = Counter(full_name, description)
        return self._counters[full_name]
    
    def gauge(self, name: str, description: str = "") -> Gauge:
        """Get or create a gauge."""
        full_name = f"{self.prefix}_{name}"
        if full_name not in self._gauges:
            self._gauges[full_name] = Gauge(full_name, description)
        return self._gauges[full_name]
    
    def histogram(self, name: str, description: str = "", buckets: tuple = None) -> Histogram:
        """Get or create a histogram."""
        full_name = f"{self.prefix}_{name}"
        if full_name not in self._histograms:
            self._histograms[full_name] = Histogram(full_name, description, buckets)
        return self._histograms[full_name]
    
    def export_prometheus(self) -> str:
        """Export all metrics in Prometheus text format."""
        lines = []
        
        for name, counter in self._counters.items():
            if counter.description:
                lines.append(f"# HELP {name} {counter.description}")
            lines.append(f"# TYPE {name} counter")
            for mv in counter.values():
                labels = ','.join(f'{k}="{v}"' for k, v in mv.labels.items())
                label_str = f"{{{labels}}}" if labels else ""
                lines.append(f"{name}{label_str} {mv.value}")
        
        for name, gauge in self._gauges.items():
            if gauge.description:
                lines.append(f"# HELP {name} {gauge.description}")
            lines.append(f"# TYPE {name} gauge")
            for mv in gauge.values():
                labels = ','.join(f'{k}="{v}"' for k, v in mv.labels.items())
                label_str = f"{{{labels}}}" if labels else ""
                lines.append(f"{name}{label_str} {mv.value}")
        
        for name, hist in self._histograms.items():
            if hist.description:
                lines.append(f"# HELP {name} {hist.description}")
            lines.append(f"# TYPE {name} histogram")
            # Simplified histogram export
            for key, counts in hist._counts.items():
                labels_dict = dict(key)
                for bucket, count in counts.items():
                    if bucket == float('inf'):
                        bucket_str = "+Inf"
                    else:
                        bucket_str = str(bucket)
                    labels = ','.join(f'{k}="{v}"' for k, v in labels_dict.items())
                    if labels:
                        labels = f"{labels},le=\"{bucket_str}\""
                    else:
                        labels = f'le="{bucket_str}"'
                    lines.append(f"{name}_bucket{{{labels}}} {count}")
        
        return '\n'.join(lines)
    
    def export_json(self) -> Dict[str, Any]:
        """Export all metrics as JSON."""
        return {
            "counters": {
                name: [{"value": mv.value, "labels": mv.labels} for mv in c.values()]
                for name, c in self._counters.items()
            },
            "gauges": {
                name: [{"value": mv.value, "labels": mv.labels} for mv in g.values()]
                for name, g in self._gauges.items()
            },
            "histograms": {
                name: {
                    "buckets": h.buckets,
                    "data": [
                        {"labels": dict(key), "sum": h._sums.get(key, 0), "count": h._totals.get(key, 0)}
                        for key in h._counts.keys()
                    ]
                }
                for name, h in self._histograms.items()
            }
        }


# Global metrics registry
metrics = MetricsRegistry()

# Pre-defined metrics
memory_reads = metrics.counter("memory_reads_total", "Total memory read operations")
memory_writes = metrics.counter("memory_writes_total", "Total memory write operations")
memory_errors = metrics.counter("memory_errors_total", "Total memory errors")
memory_size = metrics.gauge("memory_size_bytes", "Current memory size")
memory_utilization = metrics.gauge("memory_utilization_ratio", "Memory utilization (0-1)")
active_processes = metrics.gauge("active_processes", "Number of active supervised processes")
rpc_calls = metrics.counter("rpc_calls_total", "Total RPC calls")
rpc_latency = metrics.histogram("rpc_call_duration_seconds", "RPC call latency")


# HTTP endpoint handler
def create_metrics_routes(app, registry: MetricsRegistry = None):
    """Add metrics routes to FastAPI or Flask app."""
    registry = registry or metrics
    
    try:
        from fastapi import APIRouter, Response
        router = APIRouter()
        
        @router.get("/metrics")
        def prometheus_metrics():
            return Response(
                content=registry.export_prometheus(),
                media_type="text/plain"
            )
        
        @router.get("/metrics/json")
        def json_metrics():
            return registry.export_json()
        
        app.include_router(router)
        return router
        
    except ImportError:
        pass
    
    try:
        from flask import Response, jsonify
        
        @app.route("/metrics")
        def prometheus_metrics():
            return Response(registry.export_prometheus(), mimetype="text/plain")
        
        @app.route("/metrics/json")
        def json_metrics():
            return jsonify(registry.export_json())
            
    except ImportError:
        logger.warning("no_web_framework")
