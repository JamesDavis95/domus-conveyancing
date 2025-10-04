"""
Advanced Performance Monitoring System
Comprehensive performance optimization and monitoring for production deployment
"""

import os
import asyncio
import time
import logging
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import json
import statistics
from contextlib import contextmanager
import functools

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Represents a performance metric measurement"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}

@dataclass
class PerformanceThreshold:
    """Performance threshold configuration"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str = "greater_than"  # greater_than, less_than, equals
    window_minutes: int = 5
    min_samples: int = 3

class MetricsCollector:
    """Collect and aggregate performance metrics"""
    
    def __init__(self, retention_hours: int = 24):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=retention_hours * 3600))  # 1 per second
        self.thresholds: Dict[str, PerformanceThreshold] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.collection_interval = 1.0  # seconds
        self.running = False
        self.collection_thread = None
        
    def add_threshold(self, threshold: PerformanceThreshold):
        """Add performance threshold for monitoring"""
        self.thresholds[threshold.metric_name] = threshold
        logger.info(f"Added performance threshold: {threshold.metric_name}")
    
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        self.metrics[metric.name].append(metric)
        
        # Check thresholds
        self._check_threshold(metric.name)
    
    def _check_threshold(self, metric_name: str):
        """Check if metric exceeds thresholds"""
        if metric_name not in self.thresholds:
            return
            
        threshold = self.thresholds[metric_name]
        recent_metrics = list(self.metrics[metric_name])
        
        # Get metrics within the time window
        cutoff_time = datetime.now() - timedelta(minutes=threshold.window_minutes)
        window_metrics = [m for m in recent_metrics if m.timestamp >= cutoff_time]
        
        if len(window_metrics) < threshold.min_samples:
            return
        
        # Calculate average value in window
        avg_value = statistics.mean(m.value for m in window_metrics)
        
        # Check threshold
        alert_level = None
        if threshold.comparison == "greater_than":
            if avg_value >= threshold.critical_threshold:
                alert_level = "critical"
            elif avg_value >= threshold.warning_threshold:
                alert_level = "warning"
        elif threshold.comparison == "less_than":
            if avg_value <= threshold.critical_threshold:
                alert_level = "critical"
            elif avg_value <= threshold.warning_threshold:
                alert_level = "warning"
        
        if alert_level:
            self._create_alert(metric_name, avg_value, alert_level, threshold)
    
    def _create_alert(self, metric_name: str, value: float, level: str, threshold: PerformanceThreshold):
        """Create performance alert"""
        alert = {
            "metric_name": metric_name,
            "value": value,
            "level": level,
            "threshold_warning": threshold.warning_threshold,
            "threshold_critical": threshold.critical_threshold,
            "timestamp": datetime.now().isoformat(),
            "window_minutes": threshold.window_minutes
        }
        
        self.alerts.append(alert)
        logger.warning(f"Performance alert: {metric_name} = {value} ({level})")
        
        # Keep only recent alerts (last 100)
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    def get_metric_summary(self, metric_name: str, minutes: int = 60) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        if metric_name not in self.metrics:
            return {"error": "Metric not found"}
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [m for m in self.metrics[metric_name] if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"error": "No recent data"}
        
        values = [m.value for m in recent_metrics]
        
        return {
            "metric_name": metric_name,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "latest": values[-1],
            "unit": recent_metrics[-1].unit,
            "window_minutes": minutes
        }
    
    def start_collection(self):
        """Start automatic metrics collection"""
        if self.running:
            return
        
        self.running = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        logger.info("Started metrics collection")
    
    def stop_collection(self):
        """Stop automatic metrics collection"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("Stopped metrics collection")
    
    def _collection_loop(self):
        """Main collection loop"""
        while self.running:
            try:
                self._collect_system_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
    
    def _collect_system_metrics(self):
        """Collect system-level metrics"""
        timestamp = datetime.now()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent()
        self.record_metric(PerformanceMetric("cpu_usage_percent", cpu_percent, "%", timestamp))
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.record_metric(PerformanceMetric("memory_usage_percent", memory.percent, "%", timestamp))
        self.record_metric(PerformanceMetric("memory_available_gb", memory.available / (1024**3), "GB", timestamp))
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        self.record_metric(PerformanceMetric("disk_usage_percent", disk_percent, "%", timestamp))
        self.record_metric(PerformanceMetric("disk_free_gb", disk.free / (1024**3), "GB", timestamp))
        
        # Network I/O
        try:
            net_io = psutil.net_io_counters()
            self.record_metric(PerformanceMetric("network_bytes_sent", net_io.bytes_sent, "bytes", timestamp))
            self.record_metric(PerformanceMetric("network_bytes_recv", net_io.bytes_recv, "bytes", timestamp))
        except:
            pass  # Network metrics might not be available in all environments

class ApplicationProfiler:
    """Profile application performance"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.request_times: Dict[str, List[float]] = defaultdict(list)
        self.function_times: Dict[str, List[float]] = defaultdict(list)
        self.active_requests = 0
        
    @contextmanager
    def profile_request(self, endpoint: str):
        """Context manager to profile HTTP requests"""
        start_time = time.time()
        self.active_requests += 1
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.active_requests -= 1
            
            # Record metrics
            self.request_times[endpoint].append(duration)
            self.metrics_collector.record_metric(
                PerformanceMetric(f"request_duration_{endpoint}", duration * 1000, "ms", datetime.now())
            )
            self.metrics_collector.record_metric(
                PerformanceMetric("active_requests", self.active_requests, "count", datetime.now())
            )
    
    def profile_function(self, func_name: Optional[str] = None):
        """Decorator to profile function execution time"""
        def decorator(func: Callable):
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    self.function_times[name].append(duration)
                    self.metrics_collector.record_metric(
                        PerformanceMetric(f"function_duration_{name}", duration * 1000, "ms", datetime.now())
                    )
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    self.function_times[name].append(duration)
                    self.metrics_collector.record_metric(
                        PerformanceMetric(f"function_duration_{name}", duration * 1000, "ms", datetime.now())
                    )
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def get_slowest_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest HTTP endpoints"""
        endpoint_stats = []
        
        for endpoint, times in self.request_times.items():
            if not times:
                continue
            
            endpoint_stats.append({
                "endpoint": endpoint,
                "avg_duration_ms": statistics.mean(times) * 1000,
                "max_duration_ms": max(times) * 1000,
                "request_count": len(times),
                "p95_duration_ms": statistics.quantiles(times, n=20)[18] * 1000 if len(times) >= 20 else max(times) * 1000
            })
        
        return sorted(endpoint_stats, key=lambda x: x["avg_duration_ms"], reverse=True)[:limit]
    
    def get_slowest_functions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest functions"""
        function_stats = []
        
        for func_name, times in self.function_times.items():
            if not times:
                continue
            
            function_stats.append({
                "function": func_name,
                "avg_duration_ms": statistics.mean(times) * 1000,
                "max_duration_ms": max(times) * 1000,
                "call_count": len(times),
                "total_time_ms": sum(times) * 1000
            })
        
        return sorted(function_stats, key=lambda x: x["total_time_ms"], reverse=True)[:limit]

class DatabaseProfiler:
    """Profile database performance"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.query_times: Dict[str, List[float]] = defaultdict(list)
        self.slow_queries: List[Dict[str, Any]] = []
        self.slow_query_threshold = 1.0  # seconds
        
    @contextmanager
    def profile_query(self, query_type: str, query: str = ""):
        """Context manager to profile database queries"""
        start_time = time.time()
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            # Record metrics
            self.query_times[query_type].append(duration)
            self.metrics_collector.record_metric(
                PerformanceMetric(f"db_query_duration_{query_type}", duration * 1000, "ms", datetime.now())
            )
            
            # Track slow queries
            if duration > self.slow_query_threshold:
                self.slow_queries.append({
                    "query_type": query_type,
                    "query": query[:200] + "..." if len(query) > 200 else query,
                    "duration_ms": duration * 1000,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Keep only recent slow queries
                if len(self.slow_queries) > 100:
                    self.slow_queries = self.slow_queries[-100:]
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get database query statistics"""
        stats = {
            "query_types": {},
            "slow_queries": self.slow_queries[-10:],  # Last 10 slow queries
            "total_queries": sum(len(times) for times in self.query_times.values())
        }
        
        for query_type, times in self.query_times.items():
            if not times:
                continue
            
            stats["query_types"][query_type] = {
                "count": len(times),
                "avg_duration_ms": statistics.mean(times) * 1000,
                "max_duration_ms": max(times) * 1000,
                "total_time_ms": sum(times) * 1000,
                "slow_query_count": sum(1 for t in times if t > self.slow_query_threshold)
            }
        
        return stats

class PerformanceOptimizer:
    """Automatic performance optimization recommendations"""
    
    def __init__(self, metrics_collector: MetricsCollector, app_profiler: ApplicationProfiler, db_profiler: DatabaseProfiler):
        self.metrics_collector = metrics_collector
        self.app_profiler = app_profiler
        self.db_profiler = db_profiler
        
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze current performance and provide recommendations"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "system_health": "good",
            "issues": [],
            "recommendations": [],
            "metrics_summary": {},
            "performance_scores": {}
        }
        
        # Analyze system metrics
        cpu_summary = self.metrics_collector.get_metric_summary("cpu_usage_percent", 30)
        memory_summary = self.metrics_collector.get_metric_summary("memory_usage_percent", 30)
        disk_summary = self.metrics_collector.get_metric_summary("disk_usage_percent", 30)
        
        analysis["metrics_summary"] = {
            "cpu": cpu_summary,
            "memory": memory_summary,
            "disk": disk_summary
        }
        
        # Check system health
        if cpu_summary.get("mean", 0) > 80:
            analysis["system_health"] = "warning"
            analysis["issues"].append("High CPU usage detected")
            analysis["recommendations"].append("Consider scaling up CPU resources or optimizing CPU-intensive operations")
        
        if memory_summary.get("mean", 0) > 85:
            analysis["system_health"] = "warning"
            analysis["issues"].append("High memory usage detected")
            analysis["recommendations"].append("Consider increasing memory or optimizing memory usage")
        
        if disk_summary.get("mean", 0) > 85:
            analysis["system_health"] = "warning"
            analysis["issues"].append("High disk usage detected")
            analysis["recommendations"].append("Consider disk cleanup or expansion")
        
        # Analyze application performance
        slow_endpoints = self.app_profiler.get_slowest_endpoints(5)
        slow_functions = self.app_profiler.get_slowest_functions(5)
        
        analysis["performance_scores"]["endpoints"] = slow_endpoints
        analysis["performance_scores"]["functions"] = slow_functions
        
        # Check for slow endpoints
        for endpoint in slow_endpoints:
            if endpoint["avg_duration_ms"] > 2000:  # 2 seconds
                analysis["issues"].append(f"Slow endpoint detected: {endpoint['endpoint']}")
                analysis["recommendations"].append(f"Optimize {endpoint['endpoint']} - avg response time: {endpoint['avg_duration_ms']:.1f}ms")
        
        # Analyze database performance
        db_stats = self.db_profiler.get_query_stats()
        analysis["performance_scores"]["database"] = db_stats
        
        if db_stats["slow_queries"]:
            analysis["issues"].append(f"{len(db_stats['slow_queries'])} slow database queries detected")
            analysis["recommendations"].append("Review and optimize slow database queries")
        
        # Calculate overall performance score
        performance_score = 100
        performance_score -= len(analysis["issues"]) * 10
        performance_score -= len([e for e in slow_endpoints if e["avg_duration_ms"] > 1000]) * 5
        performance_score = max(0, performance_score)
        
        analysis["performance_scores"]["overall"] = performance_score
        
        if performance_score < 70:
            analysis["system_health"] = "critical"
        elif performance_score < 85:
            analysis["system_health"] = "warning"
        
        return analysis
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get specific optimization recommendations"""
        recommendations = []
        
        # Database optimization recommendations
        db_stats = self.db_profiler.get_query_stats()
        for query_type, stats in db_stats.get("query_types", {}).items():
            if stats["avg_duration_ms"] > 500:  # 500ms threshold
                recommendations.append({
                    "type": "database",
                    "priority": "high" if stats["avg_duration_ms"] > 1000 else "medium",
                    "title": f"Optimize {query_type} queries",
                    "description": f"Average query time: {stats['avg_duration_ms']:.1f}ms",
                    "actions": [
                        "Add database indexes for frequently queried columns",
                        "Review query execution plans",
                        "Consider query result caching",
                        "Optimize WHERE clauses and JOINs"
                    ]
                })
        
        # Application optimization recommendations
        slow_endpoints = self.app_profiler.get_slowest_endpoints(3)
        for endpoint in slow_endpoints:
            if endpoint["avg_duration_ms"] > 1000:
                recommendations.append({
                    "type": "application",
                    "priority": "high" if endpoint["avg_duration_ms"] > 2000 else "medium",
                    "title": f"Optimize endpoint: {endpoint['endpoint']}",
                    "description": f"Average response time: {endpoint['avg_duration_ms']:.1f}ms",
                    "actions": [
                        "Profile endpoint code for bottlenecks",
                        "Implement response caching",
                        "Optimize data serialization",
                        "Consider async processing for heavy operations"
                    ]
                })
        
        # System optimization recommendations
        cpu_summary = self.metrics_collector.get_metric_summary("cpu_usage_percent", 60)
        memory_summary = self.metrics_collector.get_metric_summary("memory_usage_percent", 60)
        
        if cpu_summary.get("mean", 0) > 70:
            recommendations.append({
                "type": "system",
                "priority": "medium",
                "title": "CPU optimization needed",
                "description": f"Average CPU usage: {cpu_summary['mean']:.1f}%",
                "actions": [
                    "Profile CPU-intensive operations",
                    "Consider horizontal scaling",
                    "Optimize algorithms and data structures",
                    "Use async/await for I/O operations"
                ]
            })
        
        if memory_summary.get("mean", 0) > 75:
            recommendations.append({
                "type": "system",
                "priority": "medium",
                "title": "Memory optimization needed",
                "description": f"Average memory usage: {memory_summary['mean']:.1f}%",
                "actions": [
                    "Profile memory usage patterns",
                    "Implement object pooling",
                    "Optimize data caching strategies",
                    "Review memory leaks in long-running processes"
                ]
            })
        
        return sorted(recommendations, key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["priority"]], reverse=True)

class AlertManager:
    """Manage performance alerts and notifications"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alert_handlers: List[Callable] = []
        self.alert_cooldown: Dict[str, datetime] = {}
        self.cooldown_minutes = 15
        
    def add_alert_handler(self, handler: Callable):
        """Add alert notification handler"""
        self.alert_handlers.append(handler)
        
    def check_alerts(self):
        """Check for new alerts and send notifications"""
        current_time = datetime.now()
        
        for alert in self.metrics_collector.alerts:
            alert_key = f"{alert['metric_name']}_{alert['level']}"
            
            # Check cooldown
            if alert_key in self.alert_cooldown:
                if current_time - self.alert_cooldown[alert_key] < timedelta(minutes=self.cooldown_minutes):
                    continue
            
            # Send alert
            for handler in self.alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}")
            
            # Set cooldown
            self.alert_cooldown[alert_key] = current_time
    
    async def email_alert_handler(self, alert: Dict[str, Any]):
        """Send alert via email"""
        subject = f"Performance Alert: {alert['metric_name']} ({alert['level'].upper()})"
        message = f"""
Performance Alert Detected

Metric: {alert['metric_name']}
Current Value: {alert['value']:.2f}
Alert Level: {alert['level'].upper()}
Warning Threshold: {alert['threshold_warning']}
Critical Threshold: {alert['threshold_critical']}
Time Window: {alert['window_minutes']} minutes
Timestamp: {alert['timestamp']}

Please investigate this performance issue immediately.
        """.strip()
        
        # Implementation would send actual email
        logger.warning(f"EMAIL ALERT: {subject}")
    
    async def slack_alert_handler(self, alert: Dict[str, Any]):
        """Send alert to Slack"""
        color = "warning" if alert['level'] == "warning" else "danger"
        message = f"🚨 Performance Alert: {alert['metric_name']} = {alert['value']:.2f} ({alert['level'].upper()})"
        
        # Implementation would send to Slack
        logger.warning(f"SLACK ALERT: {message}")

class PerformanceMonitor:
    """Main performance monitoring system"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.app_profiler = ApplicationProfiler(self.metrics_collector)
        self.db_profiler = DatabaseProfiler(self.metrics_collector)
        self.optimizer = PerformanceOptimizer(self.metrics_collector, self.app_profiler, self.db_profiler)
        self.alert_manager = AlertManager(self.metrics_collector)
        
        self.setup_default_thresholds()
        self.setup_alert_handlers()
        
    def setup_default_thresholds(self):
        """Setup default performance thresholds"""
        thresholds = [
            PerformanceThreshold("cpu_usage_percent", 75, 90, "greater_than", 5, 3),
            PerformanceThreshold("memory_usage_percent", 80, 95, "greater_than", 5, 3),
            PerformanceThreshold("disk_usage_percent", 85, 95, "greater_than", 10, 2),
            PerformanceThreshold("memory_available_gb", 1.0, 0.5, "less_than", 5, 3),
            PerformanceThreshold("active_requests", 50, 100, "greater_than", 2, 5),
        ]
        
        for threshold in thresholds:
            self.metrics_collector.add_threshold(threshold)
    
    def setup_alert_handlers(self):
        """Setup alert notification handlers"""
        self.alert_manager.add_alert_handler(self.alert_manager.email_alert_handler)
        self.alert_manager.add_alert_handler(self.alert_manager.slack_alert_handler)
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.metrics_collector.start_collection()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.metrics_collector.stop_collection()
        logger.info("Performance monitoring stopped")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for performance dashboard"""
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": {},
            "application_performance": {},
            "database_performance": {},
            "alerts": self.metrics_collector.alerts[-10:],  # Last 10 alerts
            "recommendations": self.optimizer.get_optimization_recommendations()[:5],
            "health_score": 0
        }
        
        # System metrics
        for metric_name in ["cpu_usage_percent", "memory_usage_percent", "disk_usage_percent"]:
            summary = self.metrics_collector.get_metric_summary(metric_name, 60)
            if "error" not in summary:
                dashboard["system_metrics"][metric_name] = summary
        
        # Application performance
        dashboard["application_performance"] = {
            "slow_endpoints": self.app_profiler.get_slowest_endpoints(5),
            "slow_functions": self.app_profiler.get_slowest_functions(5),
            "active_requests": self.app_profiler.active_requests
        }
        
        # Database performance
        dashboard["database_performance"] = self.db_profiler.get_query_stats()
        
        # Performance analysis
        analysis = self.optimizer.analyze_performance()
        dashboard["health_score"] = analysis["performance_scores"]["overall"]
        dashboard["system_health"] = analysis["system_health"]
        
        return dashboard
    
    def run_performance_check(self) -> Dict[str, Any]:
        """Run comprehensive performance check"""
        check_result = {
            "timestamp": datetime.now().isoformat(),
            "status": "pass",
            "checks": {},
            "summary": {},
            "recommendations": []
        }
        
        # System resource checks
        cpu_summary = self.metrics_collector.get_metric_summary("cpu_usage_percent", 10)
        memory_summary = self.metrics_collector.get_metric_summary("memory_usage_percent", 10)
        
        # CPU check
        if "error" not in cpu_summary:
            cpu_status = "pass"
            if cpu_summary["mean"] > 90:
                cpu_status = "fail"
                check_result["status"] = "fail"
            elif cpu_summary["mean"] > 75:
                cpu_status = "warning"
                if check_result["status"] == "pass":
                    check_result["status"] = "warning"
            
            check_result["checks"]["cpu_usage"] = {
                "status": cpu_status,
                "value": cpu_summary["mean"],
                "threshold_warning": 75,
                "threshold_critical": 90
            }
        
        # Memory check
        if "error" not in memory_summary:
            memory_status = "pass"
            if memory_summary["mean"] > 95:
                memory_status = "fail"
                check_result["status"] = "fail"
            elif memory_summary["mean"] > 80:
                memory_status = "warning"
                if check_result["status"] == "pass":
                    check_result["status"] = "warning"
            
            check_result["checks"]["memory_usage"] = {
                "status": memory_status,
                "value": memory_summary["mean"],
                "threshold_warning": 80,
                "threshold_critical": 95
            }
        
        # Application performance check
        slow_endpoints = self.app_profiler.get_slowest_endpoints(3)
        endpoint_status = "pass"
        
        for endpoint in slow_endpoints:
            if endpoint["avg_duration_ms"] > 3000:
                endpoint_status = "fail"
                check_result["status"] = "fail"
                break
            elif endpoint["avg_duration_ms"] > 1500:
                endpoint_status = "warning"
                if check_result["status"] == "pass":
                    check_result["status"] = "warning"
        
        check_result["checks"]["response_times"] = {
            "status": endpoint_status,
            "slowest_endpoint": slow_endpoints[0] if slow_endpoints else None,
            "threshold_warning": 1500,
            "threshold_critical": 3000
        }
        
        # Database performance check
        db_stats = self.db_profiler.get_query_stats()
        db_status = "pass"
        
        slow_query_count = len(db_stats.get("slow_queries", []))
        if slow_query_count > 10:
            db_status = "fail"
            check_result["status"] = "fail"
        elif slow_query_count > 5:
            db_status = "warning"
            if check_result["status"] == "pass":
                check_result["status"] = "warning"
        
        check_result["checks"]["database_performance"] = {
            "status": db_status,
            "slow_query_count": slow_query_count,
            "threshold_warning": 5,
            "threshold_critical": 10
        }
        
        # Summary
        check_result["summary"] = {
            "total_checks": len(check_result["checks"]),
            "passed": sum(1 for c in check_result["checks"].values() if c["status"] == "pass"),
            "warnings": sum(1 for c in check_result["checks"].values() if c["status"] == "warning"),
            "failures": sum(1 for c in check_result["checks"].values() if c["status"] == "fail")
        }
        
        # Get recommendations
        check_result["recommendations"] = self.optimizer.get_optimization_recommendations()[:3]
        
        return check_result

# Global performance monitor instance
performance_monitor = PerformanceMonitor()