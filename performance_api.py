"""
Performance Monitoring API
REST API endpoints for performance monitoring and production readiness validation
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
import asyncio
import logging
from datetime import datetime, timedelta

from performance_monitoring import performance_monitor, PerformanceThreshold, PerformanceMetric
from production_readiness import validate_production_readiness, ProductionReadinessValidator, DeploymentEnvironment

logger = logging.getLogger(__name__)

# Create router
performance_router = APIRouter(prefix="/api/v1/performance", tags=["Performance Monitoring"])

@performance_router.get("/health")
async def performance_health():
    """Performance monitoring system health check"""
    try:
        dashboard_data = performance_monitor.get_dashboard_data()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "monitoring_active": performance_monitor.metrics_collector.running,
            "health_score": dashboard_data.get("health_score", 0),
            "system_health": dashboard_data.get("system_health", "unknown"),
            "metrics_collected": len(performance_monitor.metrics_collector.metrics),
            "alerts_count": len(performance_monitor.metrics_collector.alerts)
        }
    except Exception as e:
        logger.error(f"Performance health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Performance monitoring unavailable: {str(e)}")

@performance_router.post("/monitoring/start")
async def start_monitoring():
    """Start performance monitoring"""
    try:
        if performance_monitor.metrics_collector.running:
            return {
                "status": "already_running",
                "message": "Performance monitoring is already active",
                "timestamp": datetime.now().isoformat()
            }
        
        performance_monitor.start_monitoring()
        
        return {
            "status": "started",
            "message": "Performance monitoring started successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")

@performance_router.post("/monitoring/stop")
async def stop_monitoring():
    """Stop performance monitoring"""
    try:
        if not performance_monitor.metrics_collector.running:
            return {
                "status": "already_stopped",
                "message": "Performance monitoring is not running",
                "timestamp": datetime.now().isoformat()
            }
        
        performance_monitor.stop_monitoring()
        
        return {
            "status": "stopped",
            "message": "Performance monitoring stopped successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")

@performance_router.get("/metrics")
async def get_metrics(
    metric_name: Optional[str] = Query(None, description="Specific metric name to retrieve"),
    minutes: int = Query(60, description="Time window in minutes", ge=1, le=1440)
):
    """Get performance metrics"""
    try:
        if metric_name:
            # Get specific metric
            summary = performance_monitor.metrics_collector.get_metric_summary(metric_name, minutes)
            if "error" in summary:
                raise HTTPException(status_code=404, detail=f"Metric '{metric_name}' not found")
            return summary
        else:
            # Get all available metrics
            available_metrics = list(performance_monitor.metrics_collector.metrics.keys())
            metrics_data = {}
            
            for metric in available_metrics:
                summary = performance_monitor.metrics_collector.get_metric_summary(metric, minutes)
                if "error" not in summary:
                    metrics_data[metric] = summary
            
            return {
                "timestamp": datetime.now().isoformat(),
                "window_minutes": minutes,
                "available_metrics": available_metrics,
                "metrics": metrics_data
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")

@performance_router.post("/metrics/record")
async def record_metric(
    name: str,
    value: float,
    unit: str,
    tags: Optional[Dict[str, str]] = None
):
    """Record a custom performance metric"""
    try:
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        
        performance_monitor.metrics_collector.record_metric(metric)
        
        return {
            "status": "recorded",
            "metric": {
                "name": name,
                "value": value,
                "unit": unit,
                "timestamp": metric.timestamp.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to record metric: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record metric: {str(e)}")

@performance_router.get("/thresholds")
async def get_thresholds():
    """Get performance thresholds"""
    try:
        thresholds = {}
        for name, threshold in performance_monitor.metrics_collector.thresholds.items():
            thresholds[name] = {
                "metric_name": threshold.metric_name,
                "warning_threshold": threshold.warning_threshold,
                "critical_threshold": threshold.critical_threshold,
                "comparison": threshold.comparison,
                "window_minutes": threshold.window_minutes,
                "min_samples": threshold.min_samples
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "thresholds": thresholds,
            "total_thresholds": len(thresholds)
        }
    except Exception as e:
        logger.error(f"Failed to get thresholds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve thresholds: {str(e)}")

@performance_router.post("/thresholds")
async def add_threshold(
    metric_name: str,
    warning_threshold: float,
    critical_threshold: float,
    comparison: str = "greater_than",
    window_minutes: int = 5,
    min_samples: int = 3
):
    """Add or update a performance threshold"""
    try:
        if comparison not in ["greater_than", "less_than", "equals"]:
            raise HTTPException(status_code=400, detail="Comparison must be 'greater_than', 'less_than', or 'equals'")
        
        threshold = PerformanceThreshold(
            metric_name=metric_name,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            comparison=comparison,
            window_minutes=window_minutes,
            min_samples=min_samples
        )
        
        performance_monitor.metrics_collector.add_threshold(threshold)
        
        return {
            "status": "added",
            "threshold": {
                "metric_name": metric_name,
                "warning_threshold": warning_threshold,
                "critical_threshold": critical_threshold,
                "comparison": comparison,
                "window_minutes": window_minutes,
                "min_samples": min_samples
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add threshold: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add threshold: {str(e)}")

@performance_router.get("/alerts")
async def get_alerts(
    limit: int = Query(50, description="Maximum number of alerts to return", ge=1, le=1000),
    level: Optional[str] = Query(None, description="Filter by alert level (warning, critical)")
):
    """Get performance alerts"""
    try:
        alerts = performance_monitor.metrics_collector.alerts
        
        # Filter by level if specified
        if level:
            alerts = [alert for alert in alerts if alert.get("level") == level.lower()]
        
        # Apply limit
        alerts = alerts[-limit:] if len(alerts) > limit else alerts
        
        return {
            "timestamp": datetime.now().isoformat(),
            "alerts": alerts,
            "total_alerts": len(performance_monitor.metrics_collector.alerts),
            "filtered_count": len(alerts)
        }
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alerts: {str(e)}")

@performance_router.delete("/alerts")
async def clear_alerts():
    """Clear all performance alerts"""
    try:
        cleared_count = len(performance_monitor.metrics_collector.alerts)
        performance_monitor.metrics_collector.alerts.clear()
        
        return {
            "status": "cleared",
            "cleared_count": cleared_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to clear alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear alerts: {str(e)}")

@performance_router.get("/dashboard")
async def get_dashboard():
    """Get performance dashboard data"""
    try:
        dashboard_data = performance_monitor.get_dashboard_data()
        return dashboard_data
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard data: {str(e)}")

@performance_router.get("/analysis")
async def get_performance_analysis():
    """Get performance analysis and recommendations"""
    try:
        analysis = performance_monitor.optimizer.analyze_performance()
        return analysis
    except Exception as e:
        logger.error(f"Failed to get performance analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze performance: {str(e)}")

@performance_router.get("/recommendations")
async def get_recommendations():
    """Get performance optimization recommendations"""
    try:
        recommendations = performance_monitor.optimizer.get_optimization_recommendations()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "recommendations": recommendations,
            "total_recommendations": len(recommendations)
        }
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recommendations: {str(e)}")

@performance_router.post("/check")
async def run_performance_check():
    """Run comprehensive performance check"""
    try:
        check_result = performance_monitor.run_performance_check()
        return check_result
    except Exception as e:
        logger.error(f"Performance check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Performance check failed: {str(e)}")

@performance_router.get("/profile/endpoints")
async def get_endpoint_performance():
    """Get endpoint performance statistics"""
    try:
        slow_endpoints = performance_monitor.app_profiler.get_slowest_endpoints(20)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "endpoints": slow_endpoints,
            "total_endpoints": len(performance_monitor.app_profiler.request_times),
            "active_requests": performance_monitor.app_profiler.active_requests
        }
    except Exception as e:
        logger.error(f"Failed to get endpoint performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve endpoint performance: {str(e)}")

@performance_router.get("/profile/functions")
async def get_function_performance():
    """Get function performance statistics"""
    try:
        slow_functions = performance_monitor.app_profiler.get_slowest_functions(20)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "functions": slow_functions,
            "total_functions": len(performance_monitor.app_profiler.function_times)
        }
    except Exception as e:
        logger.error(f"Failed to get function performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve function performance: {str(e)}")

@performance_router.get("/profile/database")
async def get_database_performance():
    """Get database performance statistics"""
    try:
        db_stats = performance_monitor.db_profiler.get_query_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            **db_stats
        }
    except Exception as e:
        logger.error(f"Failed to get database performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve database performance: {str(e)}")

# Production Readiness Endpoints

@performance_router.post("/readiness/validate")
async def validate_readiness(
    environment_name: str = "production",
    base_url: str = "http://localhost:8000",
    background_tasks: BackgroundTasks = None
):
    """Run production readiness validation"""
    try:
        # Run validation asynchronously
        validation_result = await validate_production_readiness(environment_name, base_url)
        
        return {
            "status": "completed",
            "validation_result": validation_result
        }
    except Exception as e:
        logger.error(f"Production readiness validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@performance_router.post("/readiness/validate-detailed")
async def validate_readiness_detailed(
    environment_name: str = "production",
    base_url: str = "http://localhost:8000",
    database_url: Optional[str] = None,
    redis_url: Optional[str] = None
):
    """Run detailed production readiness validation"""
    try:
        import os
        
        environment = DeploymentEnvironment(
            name=environment_name,
            base_url=base_url,
            database_url=database_url or os.getenv("DATABASE_URL", "postgresql://localhost/domus"),
            redis_url=redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        )
        
        validator = ProductionReadinessValidator(environment)
        validation_result = await validator.run_full_validation()
        
        return {
            "status": "completed",
            "validation_result": validation_result
        }
    except Exception as e:
        logger.error(f"Detailed validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Detailed validation failed: {str(e)}")

@performance_router.get("/readiness/checklist")
async def get_deployment_checklist():
    """Get deployment readiness checklist"""
    try:
        # Create a temporary validator to generate checklist
        import os
        environment = DeploymentEnvironment(
            name="production",
            base_url="http://localhost:8000",
            database_url=os.getenv("DATABASE_URL", "postgresql://localhost/domus"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379")
        )
        
        validator = ProductionReadinessValidator(environment)
        
        # Generate basic checklist without full validation
        checklist = [
            {
                "category": "Environment Setup",
                "items": [
                    {"task": "Verify Python version (3.8+)", "completed": False, "required": True},
                    {"task": "Install all dependencies", "completed": False, "required": True},
                    {"task": "Set environment variables", "completed": False, "required": True},
                    {"task": "Configure file permissions", "completed": False, "required": True}
                ]
            },
            {
                "category": "Database",
                "items": [
                    {"task": "Test database connection", "completed": False, "required": True},
                    {"task": "Run database migrations", "completed": False, "required": True},
                    {"task": "Verify database performance", "completed": False, "required": False}
                ]
            },
            {
                "category": "Application",
                "items": [
                    {"task": "Verify health endpoint", "completed": False, "required": True},
                    {"task": "Test API endpoints", "completed": False, "required": True},
                    {"task": "Check static assets", "completed": False, "required": False}
                ]
            },
            {
                "category": "Security",
                "items": [
                    {"task": "Configure HTTPS", "completed": False, "required": True},
                    {"task": "Set security headers", "completed": False, "required": False},
                    {"task": "Test authentication", "completed": False, "required": True}
                ]
            },
            {
                "category": "Performance",
                "items": [
                    {"task": "Load testing", "completed": False, "required": False},
                    {"task": "Monitor setup", "completed": True, "required": True},
                    {"task": "Backup verification", "completed": True, "required": True}
                ]
            }
        ]
        
        total_items = sum(len(category["items"]) for category in checklist)
        completed_items = sum(sum(1 for item in category["items"] if item["completed"]) for category in checklist)
        required_items = sum(sum(1 for item in category["items"] if item["required"]) for category in checklist)
        completed_required = sum(sum(1 for item in category["items"] if item["completed"] and item["required"]) for category in checklist)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "checklist": checklist,
            "summary": {
                "total_items": total_items,
                "completed_items": completed_items,
                "required_items": required_items,
                "completed_required": completed_required,
                "completion_percentage": (completed_items / total_items * 100) if total_items > 0 else 0,
                "required_completion_percentage": (completed_required / required_items * 100) if required_items > 0 else 0
            }
        }
    except Exception as e:
        logger.error(f"Failed to get deployment checklist: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve checklist: {str(e)}")

@performance_router.get("/system/resources")
async def get_system_resources():
    """Get current system resource usage"""
    try:
        import psutil
        
        # CPU information
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # Memory information
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk information
        disk = psutil.disk_usage('/')
        
        # Network information
        try:
            net_io = psutil.net_io_counters()
            network_stats = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
        except:
            network_stats = {"error": "Network stats unavailable"}
        
        # Process information
        process = psutil.Process()
        process_info = {
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(),
            "memory_percent": process.memory_percent(),
            "memory_info": process.memory_info()._asdict(),
            "num_threads": process.num_threads(),
            "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "usage_percent": cpu_percent,
                "count": cpu_count,
                "frequency_mhz": cpu_freq.current if cpu_freq else None
            },
            "memory": {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "used_gb": memory.used / (1024**3),
                "usage_percent": memory.percent
            },
            "swap": {
                "total_gb": swap.total / (1024**3),
                "used_gb": swap.used / (1024**3),
                "usage_percent": swap.percent
            },
            "disk": {
                "total_gb": disk.total / (1024**3),
                "used_gb": disk.used / (1024**3),
                "free_gb": disk.free / (1024**3),
                "usage_percent": (disk.used / disk.total * 100)
            },
            "network": network_stats,
            "process": process_info
        }
    except Exception as e:
        logger.error(f"Failed to get system resources: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system resources: {str(e)}")

@performance_router.get("/export/report")
async def export_performance_report(
    include_metrics: bool = True,
    include_analysis: bool = True,
    include_recommendations: bool = True,
    window_hours: int = Query(24, description="Time window for metrics in hours", ge=1, le=168)
):
    """Export comprehensive performance report"""
    try:
        report = {
            "timestamp": datetime.now().isoformat(),
            "report_window_hours": window_hours,
            "system_info": {},
            "performance_summary": {},
            "detailed_metrics": {},
            "analysis": {},
            "recommendations": []
        }
        
        # System information
        try:
            system_resources = await get_system_resources()
            report["system_info"] = system_resources.json() if hasattr(system_resources, 'json') else system_resources
        except:
            report["system_info"] = {"error": "System info unavailable"}
        
        # Performance summary
        try:
            dashboard_data = performance_monitor.get_dashboard_data()
            report["performance_summary"] = {
                "health_score": dashboard_data.get("health_score", 0),
                "system_health": dashboard_data.get("system_health", "unknown"),
                "active_requests": dashboard_data.get("application_performance", {}).get("active_requests", 0),
                "recent_alerts": len(dashboard_data.get("alerts", [])),
                "database_performance": dashboard_data.get("database_performance", {})
            }
        except:
            report["performance_summary"] = {"error": "Performance summary unavailable"}
        
        # Detailed metrics
        if include_metrics:
            try:
                metrics_data = {}
                window_minutes = window_hours * 60
                
                for metric_name in performance_monitor.metrics_collector.metrics.keys():
                    summary = performance_monitor.metrics_collector.get_metric_summary(metric_name, window_minutes)
                    if "error" not in summary:
                        metrics_data[metric_name] = summary
                
                report["detailed_metrics"] = metrics_data
            except:
                report["detailed_metrics"] = {"error": "Metrics unavailable"}
        
        # Performance analysis
        if include_analysis:
            try:
                analysis = performance_monitor.optimizer.analyze_performance()
                report["analysis"] = analysis
            except:
                report["analysis"] = {"error": "Analysis unavailable"}
        
        # Recommendations
        if include_recommendations:
            try:
                recommendations = performance_monitor.optimizer.get_optimization_recommendations()
                report["recommendations"] = recommendations
            except:
                report["recommendations"] = []
        
        return report
    except Exception as e:
        logger.error(f"Failed to export performance report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export report: {str(e)}")

# Initialize performance monitoring when module is imported
try:
    if not performance_monitor.metrics_collector.running:
        performance_monitor.start_monitoring()
        logger.info("Performance monitoring auto-started")
except Exception as e:
    logger.warning(f"Failed to auto-start performance monitoring: {e}")

# Export the router
__all__ = ["performance_router"]