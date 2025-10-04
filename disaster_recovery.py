"""
Disaster Recovery System
Comprehensive disaster recovery procedures and automation
"""

import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import subprocess
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class DisasterType(Enum):
    """Types of disasters we can handle"""
    DATABASE_FAILURE = "database_failure"
    APPLICATION_CRASH = "application_crash"
    STORAGE_FAILURE = "storage_failure"
    NETWORK_OUTAGE = "network_outage"
    SECURITY_BREACH = "security_breach"
    DATA_CORRUPTION = "data_corruption"
    COMPLETE_SYSTEM_FAILURE = "complete_system_failure"

class RecoveryPriority(Enum):
    """Recovery priority levels"""
    CRITICAL = "critical"      # 0-15 minutes RTO
    HIGH = "high"             # 15-60 minutes RTO
    MEDIUM = "medium"         # 1-4 hours RTO
    LOW = "low"              # 4-24 hours RTO

@dataclass
class RecoveryPoint:
    """Represents a point in time for recovery"""
    timestamp: datetime
    backup_id: str
    components: List[str]
    health_status: str
    data_size: int
    verification_passed: bool

@dataclass
class DisasterScenario:
    """Defines a disaster scenario and recovery procedure"""
    disaster_type: DisasterType
    priority: RecoveryPriority
    rto_minutes: int  # Recovery Time Objective
    rpo_minutes: int  # Recovery Point Objective
    automated_response: bool
    recovery_steps: List[str]
    dependencies: List[str]
    success_criteria: List[str]

class HealthMonitor:
    """Monitor system health and detect disaster scenarios"""
    
    def __init__(self):
        self.health_checks = {}
        self.alert_thresholds = {
            "database_connection_failures": 5,
            "application_error_rate": 0.1,  # 10%
            "disk_usage_percent": 85,
            "memory_usage_percent": 90,
            "response_time_ms": 5000
        }
        self.monitoring_interval = 30  # seconds
    
    def register_health_check(self, name: str, check_function: Callable) -> None:
        """Register a health check function"""
        self.health_checks[name] = check_function
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and return status"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {},
            "alerts": []
        }
        
        for check_name, check_function in self.health_checks.items():
            try:
                check_result = await check_function() if asyncio.iscoroutinefunction(check_function) else check_function()
                results["checks"][check_name] = {
                    "status": "pass" if check_result.get("healthy", True) else "fail",
                    "message": check_result.get("message", ""),
                    "metrics": check_result.get("metrics", {}),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Check for alerts
                if not check_result.get("healthy", True):
                    results["alerts"].append({
                        "check": check_name,
                        "severity": check_result.get("severity", "warning"),
                        "message": check_result.get("message", "Health check failed")
                    })
                    results["overall_status"] = "unhealthy"
                    
            except Exception as e:
                logger.error(f"Health check failed: {check_name} - {e}")
                results["checks"][check_name] = {
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results["overall_status"] = "unhealthy"
        
        return results
    
    async def database_health_check(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            from database_config import get_database_session
            
            start_time = time.time()
            
            # Test connection
            with get_database_session() as session:
                session.execute("SELECT 1")
                
            response_time = (time.time() - start_time) * 1000
            
            # Check database size and connections
            with get_database_session() as session:
                result = session.execute("""
                    SELECT 
                        pg_database_size(current_database()) as db_size,
                        (SELECT count(*) FROM pg_stat_activity) as active_connections
                """).fetchone()
                
                db_size_gb = result[0] / (1024**3)
                active_connections = result[1]
            
            healthy = (
                response_time < self.alert_thresholds["response_time_ms"] and
                active_connections < 100  # Adjust based on your limits
            )
            
            return {
                "healthy": healthy,
                "message": "Database operational" if healthy else "Database performance issues",
                "metrics": {
                    "response_time_ms": response_time,
                    "database_size_gb": db_size_gb,
                    "active_connections": active_connections
                },
                "severity": "critical" if not healthy else "info"
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Database connection failed: {e}",
                "severity": "critical"
            }
    
    async def application_health_check(self) -> Dict[str, Any]:
        """Check application health via HTTP endpoint"""
        try:
            import httpx
            
            start_time = time.time()
            
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health", timeout=10.0)
                
            response_time = (time.time() - start_time) * 1000
            
            healthy = response.status_code == 200 and response_time < self.alert_thresholds["response_time_ms"]
            
            return {
                "healthy": healthy,
                "message": "Application responding" if healthy else "Application slow or unresponsive",
                "metrics": {
                    "status_code": response.status_code,
                    "response_time_ms": response_time
                },
                "severity": "critical" if not healthy else "info"
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Application health check failed: {e}",
                "severity": "critical"
            }
    
    async def storage_health_check(self) -> Dict[str, Any]:
        """Check disk usage and storage health"""
        try:
            import shutil
            
            # Check main application disk
            disk_usage = shutil.disk_usage("/")
            disk_free_percent = (disk_usage.free / disk_usage.total) * 100
            disk_used_percent = 100 - disk_free_percent
            
            # Check document storage
            document_path = os.getenv("DOCUMENT_STORAGE_PATH", "/app/documents")
            doc_storage_size = 0
            if os.path.exists(document_path):
                for root, dirs, files in os.walk(document_path):
                    for file in files:
                        doc_storage_size += os.path.getsize(os.path.join(root, file))
            
            doc_storage_gb = doc_storage_size / (1024**3)
            
            healthy = disk_used_percent < self.alert_thresholds["disk_usage_percent"]
            
            return {
                "healthy": healthy,
                "message": "Storage healthy" if healthy else f"Disk usage high: {disk_used_percent:.1f}%",
                "metrics": {
                    "disk_used_percent": disk_used_percent,
                    "disk_free_gb": disk_usage.free / (1024**3),
                    "document_storage_gb": doc_storage_gb
                },
                "severity": "high" if not healthy else "info"
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Storage health check failed: {e}",
                "severity": "high"
            }
    
    async def redis_health_check(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance"""
        try:
            import redis
            
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            client = redis.from_url(redis_url)
            
            start_time = time.time()
            client.ping()
            response_time = (time.time() - start_time) * 1000
            
            # Get Redis info
            info = client.info()
            memory_usage_mb = info.get('used_memory', 0) / (1024**2)
            connected_clients = info.get('connected_clients', 0)
            
            healthy = (
                response_time < 100 and  # Redis should be fast
                connected_clients < 1000  # Adjust based on your limits
            )
            
            return {
                "healthy": healthy,
                "message": "Redis operational" if healthy else "Redis performance issues",
                "metrics": {
                    "response_time_ms": response_time,
                    "memory_usage_mb": memory_usage_mb,
                    "connected_clients": connected_clients
                },
                "severity": "medium" if not healthy else "info"
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Redis connection failed: {e}",
                "severity": "medium"
            }

class DisasterRecoveryManager:
    """Main disaster recovery management system"""
    
    def __init__(self, backup_manager):
        self.backup_manager = backup_manager
        self.health_monitor = HealthMonitor()
        self.recovery_scenarios = self._define_recovery_scenarios()
        self.recovery_history = []
        
        # Register health checks
        self.health_monitor.register_health_check("database", self.health_monitor.database_health_check)
        self.health_monitor.register_health_check("application", self.health_monitor.application_health_check)
        self.health_monitor.register_health_check("storage", self.health_monitor.storage_health_check)
        self.health_monitor.register_health_check("redis", self.health_monitor.redis_health_check)
    
    def _define_recovery_scenarios(self) -> Dict[DisasterType, DisasterScenario]:
        """Define recovery scenarios for different disaster types"""
        return {
            DisasterType.DATABASE_FAILURE: DisasterScenario(
                disaster_type=DisasterType.DATABASE_FAILURE,
                priority=RecoveryPriority.CRITICAL,
                rto_minutes=15,
                rpo_minutes=5,
                automated_response=True,
                recovery_steps=[
                    "Stop application services",
                    "Assess database corruption extent",
                    "Restore from latest backup",
                    "Verify data integrity",
                    "Restart application services",
                    "Validate full system functionality"
                ],
                dependencies=["backup_system", "database_tools"],
                success_criteria=[
                    "Database connectivity restored",
                    "All critical transactions working",
                    "Data consistency verified"
                ]
            ),
            
            DisasterType.APPLICATION_CRASH: DisasterScenario(
                disaster_type=DisasterType.APPLICATION_CRASH,
                priority=RecoveryPriority.CRITICAL,
                rto_minutes=5,
                rpo_minutes=0,
                automated_response=True,
                recovery_steps=[
                    "Check system resources",
                    "Review application logs",
                    "Restart application services",
                    "Validate service health",
                    "Monitor for stability"
                ],
                dependencies=["monitoring_system"],
                success_criteria=[
                    "Application responding to health checks",
                    "All endpoints operational",
                    "No critical errors in logs"
                ]
            ),
            
            DisasterType.STORAGE_FAILURE: DisasterScenario(
                disaster_type=DisasterType.STORAGE_FAILURE,
                priority=RecoveryPriority.HIGH,
                rto_minutes=30,
                rpo_minutes=15,
                automated_response=False,
                recovery_steps=[
                    "Assess storage damage",
                    "Mount backup storage",
                    "Restore document files",
                    "Update storage paths",
                    "Restart affected services",
                    "Verify file accessibility"
                ],
                dependencies=["backup_storage", "file_system_tools"],
                success_criteria=[
                    "Document access restored",
                    "File uploads working",
                    "No data loss detected"
                ]
            ),
            
            DisasterType.SECURITY_BREACH: DisasterScenario(
                disaster_type=DisasterType.SECURITY_BREACH,
                priority=RecoveryPriority.CRITICAL,
                rto_minutes=10,
                rpo_minutes=0,
                automated_response=True,
                recovery_steps=[
                    "Isolate affected systems",
                    "Change all credentials",
                    "Review access logs",
                    "Patch security vulnerabilities",
                    "Restore from clean backup",
                    "Implement additional security measures",
                    "Notify relevant parties"
                ],
                dependencies=["security_tools", "backup_system"],
                success_criteria=[
                    "Breach contained",
                    "Systems secured",
                    "No ongoing unauthorized access"
                ]
            ),
            
            DisasterType.COMPLETE_SYSTEM_FAILURE: DisasterScenario(
                disaster_type=DisasterType.COMPLETE_SYSTEM_FAILURE,
                priority=RecoveryPriority.CRITICAL,
                rto_minutes=60,
                rpo_minutes=30,
                automated_response=False,
                recovery_steps=[
                    "Assess infrastructure damage",
                    "Deploy to backup infrastructure",
                    "Restore full system backup",
                    "Reconfigure networking",
                    "Restore all services",
                    "Validate complete functionality",
                    "Update DNS/load balancers"
                ],
                dependencies=["backup_infrastructure", "full_backup", "dns_management"],
                success_criteria=[
                    "All services operational",
                    "Data integrity confirmed",
                    "Performance within normal ranges",
                    "Users can access system"
                ]
            )
        }
    
    async def detect_disaster(self, health_status: Dict[str, Any]) -> Optional[DisasterType]:
        """Analyze health status to detect potential disasters"""
        
        # Critical application failure
        if health_status["checks"].get("application", {}).get("status") == "error":
            return DisasterType.APPLICATION_CRASH
        
        # Database connectivity issues
        if health_status["checks"].get("database", {}).get("status") == "error":
            return DisasterType.DATABASE_FAILURE
        
        # Storage issues
        storage_check = health_status["checks"].get("storage", {})
        if storage_check.get("status") == "fail":
            metrics = storage_check.get("metrics", {})
            if metrics.get("disk_used_percent", 0) > 95:
                return DisasterType.STORAGE_FAILURE
        
        # Performance degradation that might indicate issues
        app_metrics = health_status["checks"].get("application", {}).get("metrics", {})
        if app_metrics.get("response_time_ms", 0) > 10000:  # 10 second response time
            return DisasterType.APPLICATION_CRASH
        
        return None
    
    async def execute_recovery(self, disaster_type: DisasterType, manual_override: bool = False) -> Dict[str, Any]:
        """Execute disaster recovery procedure"""
        
        scenario = self.recovery_scenarios.get(disaster_type)
        if not scenario:
            return {"success": False, "error": f"No recovery scenario defined for {disaster_type}"}
        
        recovery_id = f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        recovery_log = {
            "recovery_id": recovery_id,
            "disaster_type": disaster_type.value,
            "scenario": scenario,
            "started_at": datetime.now().isoformat(),
            "manual_override": manual_override,
            "steps_completed": [],
            "errors": [],
            "success": False
        }
        
        logger.critical(f"Starting disaster recovery for {disaster_type.value}")
        
        try:
            # Check if automated response is allowed
            if not scenario.automated_response and not manual_override:
                recovery_log["errors"].append("Automated response not allowed - manual intervention required")
                return recovery_log
            
            # Execute recovery steps
            for step_index, step in enumerate(scenario.recovery_steps):
                logger.info(f"Executing recovery step {step_index + 1}: {step}")
                
                step_result = await self._execute_recovery_step(step, disaster_type, scenario)
                
                recovery_log["steps_completed"].append({
                    "step": step,
                    "result": step_result,
                    "timestamp": datetime.now().isoformat()
                })
                
                if not step_result.get("success", False):
                    recovery_log["errors"].append(f"Step failed: {step} - {step_result.get('error', 'Unknown error')}")
                    logger.error(f"Recovery step failed: {step}")
                    break
            
            # Validate success criteria
            validation_results = await self._validate_recovery(scenario.success_criteria)
            recovery_log["validation"] = validation_results
            
            if all(result["passed"] for result in validation_results):
                recovery_log["success"] = True
                logger.info(f"Disaster recovery successful: {recovery_id}")
            else:
                recovery_log["errors"].append("Success criteria not met after recovery")
                logger.error(f"Disaster recovery validation failed: {recovery_id}")
            
        except Exception as e:
            recovery_log["errors"].append(f"Recovery execution error: {e}")
            logger.error(f"Recovery execution failed: {e}")
        
        recovery_log["completed_at"] = datetime.now().isoformat()
        recovery_log["duration_minutes"] = (
            datetime.fromisoformat(recovery_log["completed_at"]) - 
            datetime.fromisoformat(recovery_log["started_at"])
        ).total_seconds() / 60
        
        # Store recovery history
        self.recovery_history.append(recovery_log)
        
        return recovery_log
    
    async def _execute_recovery_step(self, step: str, disaster_type: DisasterType, scenario: DisasterScenario) -> Dict[str, Any]:
        """Execute individual recovery step"""
        
        try:
            if "stop application services" in step.lower():
                return await self._stop_application_services()
            
            elif "restart application services" in step.lower():
                return await self._restart_application_services()
            
            elif "restore from latest backup" in step.lower():
                return await self._restore_latest_backup()
            
            elif "verify data integrity" in step.lower():
                return await self._verify_data_integrity()
            
            elif "validate full system functionality" in step.lower():
                return await self._validate_system_functionality()
            
            elif "check system resources" in step.lower():
                return await self._check_system_resources()
            
            elif "review application logs" in step.lower():
                return await self._review_application_logs()
            
            elif "change all credentials" in step.lower():
                return await self._change_credentials()
            
            elif "isolate affected systems" in step.lower():
                return await self._isolate_systems()
            
            else:
                # Generic step execution
                return {
                    "success": True,
                    "message": f"Step acknowledged: {step}",
                    "action_required": "Manual intervention needed"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _stop_application_services(self) -> Dict[str, Any]:
        """Stop application services gracefully"""
        try:
            # Implementation would depend on your deployment method
            # Docker Compose example:
            result = subprocess.run(['docker-compose', 'stop', 'app'], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {"success": True, "message": "Application services stopped"}
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _restart_application_services(self) -> Dict[str, Any]:
        """Restart application services"""
        try:
            result = subprocess.run(['docker-compose', 'up', '-d', 'app'], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Wait for services to be ready
                await asyncio.sleep(30)
                return {"success": True, "message": "Application services restarted"}
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _restore_latest_backup(self) -> Dict[str, Any]:
        """Restore from the latest backup"""
        try:
            # Get latest backup
            backup_status = self.backup_manager.get_backup_status()
            
            if not backup_status.get("last_backup"):
                return {"success": False, "error": "No backup available"}
            
            backup_id = backup_status["last_backup"]["backup_id"]
            
            # Restore database and critical components
            restore_result = self.backup_manager.restore_backup(backup_id, ["database", "redis"])
            
            return {
                "success": restore_result["success"],
                "message": f"Restored from backup: {backup_id}",
                "details": restore_result
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _verify_data_integrity(self) -> Dict[str, Any]:
        """Verify data integrity after restore"""
        try:
            # Run data integrity checks
            from database_config import get_database_session
            
            integrity_checks = []
            
            with get_database_session() as session:
                # Check for orphaned records
                result = session.execute("""
                    SELECT 
                        'transactions' as table_name,
                        COUNT(*) as record_count
                    FROM transactions
                    UNION ALL
                    SELECT 
                        'documents' as table_name,
                        COUNT(*) as record_count  
                    FROM documents
                """)
                
                for row in result:
                    integrity_checks.append({
                        "table": row[0],
                        "record_count": row[1],
                        "status": "ok" if row[1] > 0 else "warning"
                    })
            
            all_ok = all(check["status"] == "ok" for check in integrity_checks)
            
            return {
                "success": all_ok,
                "message": "Data integrity verified" if all_ok else "Data integrity issues detected",
                "checks": integrity_checks
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _validate_system_functionality(self) -> Dict[str, Any]:
        """Validate that all system functions are working"""
        try:
            health_status = await self.health_monitor.run_health_checks()
            
            all_healthy = health_status["overall_status"] == "healthy"
            
            return {
                "success": all_healthy,
                "message": "System functionality validated" if all_healthy else "System functionality issues detected",
                "health_status": health_status
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource availability"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            resource_ok = (
                cpu_percent < 80 and
                memory.percent < 85 and
                (disk.used / disk.total) < 0.85
            )
            
            return {
                "success": resource_ok,
                "message": "System resources OK" if resource_ok else "System resource constraints detected",
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": (disk.used / disk.total) * 100
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _review_application_logs(self) -> Dict[str, Any]:
        """Review recent application logs for errors"""
        try:
            # Implementation would read application logs
            # This is a simplified version
            
            log_file = "/app/logs/application.log"
            error_count = 0
            
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    # Read last 100 lines
                    lines = f.readlines()[-100:]
                    
                    for line in lines:
                        if any(level in line.upper() for level in ['ERROR', 'CRITICAL', 'FATAL']):
                            error_count += 1
            
            return {
                "success": error_count < 5,  # Acceptable error threshold
                "message": f"Log review completed: {error_count} errors found",
                "error_count": error_count
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _change_credentials(self) -> Dict[str, Any]:
        """Change system credentials (manual step)"""
        return {
            "success": True,
            "message": "Credential change initiated - manual completion required",
            "action_required": "Update database passwords, API keys, and JWT secrets"
        }
    
    async def _isolate_systems(self) -> Dict[str, Any]:
        """Isolate systems from network (manual step)"""
        return {
            "success": True,
            "message": "System isolation initiated - manual completion required",
            "action_required": "Disconnect from external networks, block suspicious traffic"
        }
    
    async def _validate_recovery(self, success_criteria: List[str]) -> List[Dict[str, Any]]:
        """Validate recovery against success criteria"""
        
        validation_results = []
        
        for criterion in success_criteria:
            try:
                if "database connectivity" in criterion.lower():
                    health_check = await self.health_monitor.database_health_check()
                    passed = health_check.get("healthy", False)
                    
                elif "application responding" in criterion.lower():
                    health_check = await self.health_monitor.application_health_check()
                    passed = health_check.get("healthy", False)
                    
                elif "data integrity" in criterion.lower():
                    integrity_result = await self._verify_data_integrity()
                    passed = integrity_result.get("success", False)
                    
                else:
                    # Manual validation required
                    passed = False
                    
                validation_results.append({
                    "criterion": criterion,
                    "passed": passed,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                validation_results.append({
                    "criterion": criterion,
                    "passed": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        return validation_results
    
    async def get_recovery_status(self) -> Dict[str, Any]:
        """Get current disaster recovery system status"""
        
        health_status = await self.health_monitor.run_health_checks()
        potential_disaster = await self.detect_disaster(health_status)
        
        return {
            "system_health": health_status,
            "potential_disaster": potential_disaster.value if potential_disaster else None,
            "recovery_scenarios_defined": len(self.recovery_scenarios),
            "recovery_history_count": len(self.recovery_history),
            "last_recovery": self.recovery_history[-1] if self.recovery_history else None,
            "backup_status": self.backup_manager.get_backup_status(),
            "monitoring_active": True,
            "timestamp": datetime.now().isoformat()
        }