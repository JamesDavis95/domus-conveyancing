"""
Production Infrastructure & Monitoring System
Comprehensive health checks, error tracking, logging, and operational monitoring
"""

import os
import logging
import traceback
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from models import get_db, User, Organization, Usage
from production_auth_complete import get_current_user, require_role, UserRole
import asyncio
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class HealthCheckService:
    """System health monitoring service"""
    
    @staticmethod
    async def check_database_health(db: Session) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test basic query
            result = db.execute(text("SELECT 1")).scalar()
            query_time = time.time() - start_time
            
            # Check table counts
            user_count = db.query(User).count()
            org_count = db.query(Organization).count()
            
            return {
                "status": "healthy",
                "response_time_ms": round(query_time * 1000, 2),
                "user_count": user_count,
                "organization_count": org_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    async def check_system_resources() -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy",
                "cpu_usage_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "percent": round((disk.used / disk.total) * 100, 2)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"System resource check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    async def check_external_services() -> Dict[str, Any]:
        """Check external service connectivity"""
        services = {
            "stripe": "https://api.stripe.com/v1/account",
            "planning_portal": "https://www.planningportal.co.uk",
            "os_maps": "https://api.os.uk/maps/raster/v1"
        }
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for service_name, url in services.items():
                try:
                    start_time = time.time()
                    async with session.get(url, timeout=10) as response:
                        response_time = time.time() - start_time
                        results[service_name] = {
                            "status": "healthy" if response.status < 500 else "unhealthy",
                            "response_time_ms": round(response_time * 1000, 2),
                            "status_code": response.status
                        }
                except Exception as e:
                    results[service_name] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
        
        return {
            "services": results,
            "timestamp": datetime.utcnow().isoformat()
        }

class ErrorTrackingService:
    """Error tracking and alerting service"""
    
    @staticmethod
    async def log_error(
        error_type: str,
        message: str,
        user_id: Optional[int] = None,
        request_path: Optional[str] = None,
        stack_trace: Optional[str] = None
    ):
        """Log application error"""
        error_data = {
            "error_type": error_type,
            "message": message,
            "user_id": user_id,
            "request_path": request_path,
            "stack_trace": stack_trace,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.error(f"Application Error: {error_data}")
        
        # Send alert if critical error
        if error_type in ["database_error", "payment_failure", "auth_failure"]:
            await ErrorTrackingService._send_alert(error_data)
    
    @staticmethod
    async def _send_alert(error_data: Dict[str, Any]):
        """Send error alert to operations team"""
        try:
            # Email configuration
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER', 'alerts@domusplanning.co.uk')
            smtp_password = os.getenv('SMTP_PASSWORD', 'your-app-password')
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = 'ops@domusplanning.co.uk'
            msg['Subject'] = f"CRITICAL: {error_data['error_type']} - Domus Platform"
            
            body = f"""
            Critical error detected on Domus Planning Platform:
            
            Error Type: {error_data['error_type']}
            Message: {error_data['message']}
            User ID: {error_data.get('user_id', 'N/A')}
            Request Path: {error_data.get('request_path', 'N/A')}
            Timestamp: {error_data['timestamp']}
            
            Stack Trace:
            {error_data.get('stack_trace', 'N/A')}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Error alert sent for {error_data['error_type']}")
            
        except Exception as e:
            logger.error(f"Failed to send error alert: {str(e)}")

class BackupService:
    """Database backup and recovery service"""
    
    @staticmethod
    async def create_backup(backup_type: str = "daily") -> Dict[str, Any]:
        """Create database backup"""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"domus_backup_{backup_type}_{timestamp}.sql"
            backup_path = f"/backups/{backup_filename}"
            
            # Create backup directory
            os.makedirs("/backups", exist_ok=True)
            
            # Create SQLite backup (for production, use appropriate DB backup commands)
            import shutil
            shutil.copy2("production.db", backup_path.replace(".sql", ".db"))
            
            logger.info(f"Backup created: {backup_filename}")
            
            return {
                "status": "success",
                "backup_file": backup_filename,
                "backup_path": backup_path,
                "size_mb": os.path.getsize(backup_path.replace(".sql", ".db")) / (1024 * 1024),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            await ErrorTrackingService.log_error(
                "backup_failure",
                f"Database backup failed: {str(e)}",
                stack_trace=traceback.format_exc()
            )
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    async def cleanup_old_backups(retention_days: int = 30):
        """Clean up old backup files"""
        try:
            backup_dir = "/backups"
            if not os.path.exists(backup_dir):
                return
            
            cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
            deleted_count = 0
            
            for filename in os.listdir(backup_dir):
                filepath = os.path.join(backup_dir, filename)
                if os.path.getctime(filepath) < cutoff_time:
                    os.remove(filepath)
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old backup files")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {str(e)}")

class PerformanceMonitor:
    """Application performance monitoring"""
    
    @staticmethod
    async def get_performance_metrics(db: Session) -> Dict[str, Any]:
        """Get application performance metrics"""
        try:
            # API usage in last 24 hours
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_usage = db.query(Usage).filter(Usage.created_at >= yesterday).count()
            
            # Usage by resource type
            usage_by_type = db.query(
                Usage.resource_type, 
                func.count(Usage.id).label('count')
            ).filter(
                Usage.created_at >= yesterday
            ).group_by(Usage.resource_type).all()
            
            # Active organizations
            active_orgs = db.query(Organization).filter(
                Organization.subscription_status == "active"
            ).count()
            
            # System metrics
            system_metrics = await HealthCheckService.check_system_resources()
            
            return {
                "api_metrics": {
                    "total_requests_24h": recent_usage,
                    "usage_by_type": {item.resource_type: item.count for item in usage_by_type}
                },
                "business_metrics": {
                    "active_organizations": active_orgs,
                    "total_organizations": db.query(Organization).count(),
                    "total_users": db.query(User).count()
                },
                "system_metrics": system_metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Performance metrics collection failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Background tasks
async def scheduled_health_checks():
    """Run scheduled health checks"""
    while True:
        try:
            logger.info("Running scheduled health checks...")
            
            # Database health check
            db_session = next(get_db())
            db_health = await HealthCheckService.check_database_health(db_session)
            
            if db_health["status"] == "unhealthy":
                await ErrorTrackingService.log_error(
                    "database_error",
                    f"Database health check failed: {db_health.get('error', 'Unknown error')}"
                )
            
            # System resource check
            system_health = await HealthCheckService.check_system_resources()
            
            # Alert on high resource usage
            if system_health.get("cpu_usage_percent", 0) > 90:
                await ErrorTrackingService.log_error(
                    "high_cpu_usage",
                    f"CPU usage is {system_health['cpu_usage_percent']}%"
                )
            
            if system_health.get("memory", {}).get("percent", 0) > 90:
                await ErrorTrackingService.log_error(
                    "high_memory_usage",
                    f"Memory usage is {system_health['memory']['percent']}%"
                )
            
            # Daily backup
            current_hour = datetime.utcnow().hour
            if current_hour == 2:  # 2 AM UTC
                await BackupService.create_backup("daily")
                await BackupService.cleanup_old_backups()
            
            db_session.close()
            
        except Exception as e:
            logger.error(f"Scheduled health check failed: {str(e)}")
        
        # Wait 5 minutes before next check
        await asyncio.sleep(300)

# API endpoints
class MonitoringAPI:
    """Monitoring and operational API endpoints"""
    
    @staticmethod
    async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
        """Public health check endpoint"""
        db_health = await HealthCheckService.check_database_health(db)
        system_health = await HealthCheckService.check_system_resources()
        
        overall_status = "healthy" if (
            db_health["status"] == "healthy" and 
            system_health["status"] == "healthy"
        ) else "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "4.0.0",
            "checks": {
                "database": db_health,
                "system": system_health
            }
        }
    
    @staticmethod
    async def detailed_status(
        current_user: User = Depends(require_role(UserRole.ADMIN)),
        db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        """Detailed system status for administrators"""
        db_health = await HealthCheckService.check_database_health(db)
        system_health = await HealthCheckService.check_system_resources()
        external_health = await HealthCheckService.check_external_services()
        performance_metrics = await PerformanceMonitor.get_performance_metrics(db)
        
        return {
            "overall_status": "healthy",  # TODO: Calculate based on all checks
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_health,
            "system": system_health,
            "external_services": external_health,
            "performance": performance_metrics
        }
    
    @staticmethod
    async def create_manual_backup(
        background_tasks: BackgroundTasks,
        current_user: User = Depends(require_role(UserRole.ADMIN))
    ) -> Dict[str, Any]:
        """Create manual backup"""
        background_tasks.add_task(BackupService.create_backup, "manual")
        return {
            "message": "Backup initiated",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def get_logs(
        lines: int = 100,
        level: str = "INFO",
        current_user: User = Depends(require_role(UserRole.ADMIN))
    ) -> Dict[str, Any]:
        """Get recent application logs"""
        try:
            with open("production.log", "r") as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                # Filter by log level if specified
                if level != "ALL":
                    filtered_lines = [line for line in recent_lines if level in line]
                    recent_lines = filtered_lines
                
                return {
                    "logs": recent_lines,
                    "total_lines": len(recent_lines),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read logs: {str(e)}"
            )

# Error handling middleware
async def error_handling_middleware(request: Request, call_next):
    """Global error handling middleware"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        # Log the error
        await ErrorTrackingService.log_error(
            "unhandled_exception",
            str(e),
            request_path=str(request.url),
            stack_trace=traceback.format_exc()
        )
        
        # Return generic error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }
        )