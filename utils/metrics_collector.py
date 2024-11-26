"""Metrics collection utility for monitoring system performance."""

import logging
from typing import Dict, Any
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, Summary

class MetricsCollector:
    """Collects and manages system metrics."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._init_metrics()
        
    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        # Performance metrics
        self.request_latency = Histogram(
            'request_latency_seconds',
            'Request latency in seconds',
            ['endpoint']
        )
        
        self.request_count = Counter(
            'request_total',
            'Total number of requests',
            ['endpoint', 'status']
        )
        
        # Business metrics
        self.leads_discovered = Counter(
            'leads_discovered_total',
            'Total number of leads discovered',
            ['source']
        )
        
        self.engagement_attempts = Counter(
            'engagement_attempts_total',
            'Total number of engagement attempts',
            ['channel']
        )
        
        self.engagement_success = Counter(
            'engagement_success_total',
            'Total number of successful engagements',
            ['channel']
        )
        
        # Resource metrics
        self.active_connections = Gauge(
            'active_connections',
            'Number of active connections',
            ['type']
        )
        
        self.processing_time = Summary(
            'task_processing_seconds',
            'Time spent processing tasks',
            ['task_type']
        )
        
    def track_request(self, endpoint: str, status: str, duration: float):
        """Track API request metrics."""
        try:
            self.request_latency.labels(endpoint=endpoint).observe(duration)
            self.request_count.labels(endpoint=endpoint, status=status).inc()
        except Exception as e:
            self.logger.error(f"Error tracking request metrics: {str(e)}")
            
    def track_lead_discovery(self, source: str):
        """Track lead discovery metrics."""
        try:
            self.leads_discovered.labels(source=source).inc()
        except Exception as e:
            self.logger.error(f"Error tracking lead discovery: {str(e)}")
            
    def track_engagement(self, channel: str, success: bool):
        """Track engagement metrics."""
        try:
            self.engagement_attempts.labels(channel=channel).inc()
            if success:
                self.engagement_success.labels(channel=channel).inc()
        except Exception as e:
            self.logger.error(f"Error tracking engagement: {str(e)}")
            
    def update_connections(self, conn_type: str, count: int):
        """Update active connection count."""
        try:
            self.active_connections.labels(type=conn_type).set(count)
        except Exception as e:
            self.logger.error(f"Error updating connection count: {str(e)}")
            
    def track_processing_time(self, task_type: str, duration: float):
        """Track task processing time."""
        try:
            self.processing_time.labels(task_type=task_type).observe(duration)
        except Exception as e:
            self.logger.error(f"Error tracking processing time: {str(e)}")
            
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics."""
        try:
            return {
                'total_leads': self.leads_discovered._value.sum(),
                'total_engagements': self.engagement_attempts._value.sum(),
                'success_rate': (
                    self.engagement_success._value.sum() /
                    self.engagement_attempts._value.sum()
                    if self.engagement_attempts._value.sum() > 0 else 0
                ),
                'avg_latency': self.request_latency._sum.sum() / self.request_latency._count.sum()
                if self.request_latency._count.sum() > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Error generating metrics summary: {str(e)}")
            return {}
