"""
Monitoring utilities for metric store operations
"""

import time
import logging
from functools import wraps
from typing import Callable, Any
import os

logger = logging.getLogger(__name__)

# Prometheus metrics (if available)
try:
    from prometheus_client import Gauge, Counter, Histogram
    
    # Define metrics
    metric_ingest_duration = Histogram(
        'metric_ingest_seconds',
        'Time spent ingesting metrics from Excel',
        ['workspace_id', 'template_type']
    )
    
    metric_ingest_count = Counter(
        'metric_ingest_total',
        'Total number of metrics ingested',
        ['workspace_id', 'status']
    )
    
    metric_store_size = Gauge(
        'metric_store_rows',
        'Number of rows in metric store',
        ['workspace_id']
    )
    
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.info("Prometheus client not available - metrics disabled")

def monitor_ingestion(func: Callable) -> Callable:
    """
    Decorator to monitor metric ingestion performance
    Tracks duration and success/failure counts
    """
    @wraps(func)
    def wrapper(workspace_id: str, excel_path: str, *args, **kwargs) -> Any:
        start_time = time.time()
        template_type = "unknown"
        
        # Try to detect template type from filename
        if "3statement" in excel_path.lower():
            template_type = "3statement"
        elif "kpi" in excel_path.lower():
            template_type = "kpi_dashboard"
        elif "board" in excel_path.lower():
            template_type = "board_pack"
        
        try:
            # Call the actual function
            result = func(workspace_id, excel_path, *args, **kwargs)
            
            # Record success metrics
            duration = time.time() - start_time
            
            if PROMETHEUS_AVAILABLE:
                metric_ingest_duration.labels(
                    workspace_id=workspace_id,
                    template_type=template_type
                ).observe(duration)
                
                metric_ingest_count.labels(
                    workspace_id=workspace_id,
                    status="success"
                ).inc()
            
            # Log performance
            logger.info(
                f"Metric ingestion completed in {duration:.2f}s - "
                f"workspace: {workspace_id}, template: {template_type}, "
                f"metrics: {result.get('extracted', 0)}"
            )
            
            # Emit custom metric event (for DataDog, New Relic, etc.)
            emit_metric_event(
                "metric.ingest.duration",
                duration,
                tags={
                    "workspace": workspace_id,
                    "template": template_type,
                    "metrics_count": result.get('extracted', 0)
                }
            )
            
            return result
            
        except Exception as e:
            # Record failure
            duration = time.time() - start_time
            
            if PROMETHEUS_AVAILABLE:
                metric_ingest_count.labels(
                    workspace_id=workspace_id,
                    status="failure"
                ).inc()
            
            logger.error(
                f"Metric ingestion failed after {duration:.2f}s - "
                f"workspace: {workspace_id}, error: {str(e)}"
            )
            
            # Re-raise the exception
            raise
    
    return wrapper

def emit_metric_event(metric_name: str, value: float, tags: dict = None):
    """
    Emit custom metric event to monitoring service
    This is a placeholder for integration with DataDog, New Relic, etc.
    """
    if os.getenv("MONITORING_ENABLED", "false").lower() == "true":
        # Example: DataDog
        # from datadog import statsd
        # statsd.gauge(metric_name, value, tags=tags)
        
        # Example: New Relic
        # import newrelic.agent
        # newrelic.agent.record_custom_metric(metric_name, value)
        
        # For now, just log
        logger.debug(f"Metric event: {metric_name}={value}, tags={tags}")

def update_metric_store_size(workspace_id: str, count: int):
    """Update the metric store size gauge"""
    if PROMETHEUS_AVAILABLE:
        metric_store_size.labels(workspace_id=workspace_id).set(count)

# Export decorated version of ingest_metrics
from metrics.ingest import ingest_metrics as _ingest_metrics
ingest_metrics_monitored = monitor_ingestion(_ingest_metrics)