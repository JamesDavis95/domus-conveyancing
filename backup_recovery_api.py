"""
Backup and Recovery API Endpoints
FastAPI endpoints for managing backup and disaster recovery operations
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime

from backup_system import BackupManager, BackupConfig
from disaster_recovery import DisasterRecoveryManager, DisasterType
from business_continuity import BusinessContinuityManager

# Initialize systems
backup_config = BackupConfig()
backup_manager = BackupManager(backup_config)
disaster_recovery = DisasterRecoveryManager(backup_manager)
business_continuity = BusinessContinuityManager()

router = APIRouter(prefix="/api/backup-recovery", tags=["backup", "recovery"])

# Backup Endpoints

@router.post("/backup/create")
async def create_backup(
    backup_type: str = Query("manual", description="Type of backup: daily, weekly, monthly, manual"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Create a new system backup"""
    
    def run_backup():
        return backup_manager.create_full_backup(backup_type)
    
    # Run backup in background for large operations
    if backup_type in ["weekly", "monthly"]:
        background_tasks.add_task(run_backup)
        return {
            "message": f"{backup_type.capitalize()} backup started in background",
            "backup_type": backup_type,
            "started_at": datetime.now().isoformat()
        }
    else:
        # Run immediately for daily/manual backups
        result = run_backup()
        return result

@router.get("/backup/status")
async def get_backup_status():
    """Get comprehensive backup system status"""
    
    status = backup_manager.get_backup_status()
    
    # Add health information
    health_status = await disaster_recovery.health_monitor.run_health_checks()
    status["system_health"] = health_status["overall_status"]
    status["health_alerts"] = len(health_status.get("alerts", []))
    
    return status

@router.get("/backup/list")
async def list_backups(
    backup_type: Optional[str] = Query(None, description="Filter by backup type"),
    limit: int = Query(50, description="Maximum number of backups to return")
):
    """List available backups"""
    
    status = backup_manager.get_backup_status()
    
    # This would be expanded to actually list and filter backups
    return {
        "backups": [],  # Would contain actual backup list
        "total_count": status.get("backup_count", 0),
        "total_size": status.get("total_backup_size", 0),
        "storage_locations": status.get("storage_locations", [])
    }

@router.post("/backup/restore")
async def restore_backup(
    backup_id: str,
    components: List[str] = Query(None, description="Components to restore: database, redis, documents, config"),
    confirm: bool = Query(False, description="Confirmation required for restore operation")
):
    """Restore from backup"""
    
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Restore operation requires explicit confirmation. Set confirm=true"
        )
    
    if not components:
        components = ["database", "redis", "documents"]  # Default safe components
    
    try:
        result = backup_manager.restore_backup(backup_id, components)
        
        if result["success"]:
            return {
                "message": "Restore completed successfully",
                "backup_id": backup_id,
                "restored_components": result["restored_components"],
                "completed_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=f"Restore failed: {result.get('errors', [])}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore operation failed: {str(e)}")

@router.post("/backup/cleanup")
async def cleanup_old_backups():
    """Clean up old backups based on retention policy"""
    
    try:
        backup_manager.cleanup_old_backups()
        return {
            "message": "Backup cleanup completed",
            "retention_policy": {
                "daily": f"{backup_config.daily_retention_days} days",
                "weekly": f"{backup_config.weekly_retention_weeks} weeks",
                "monthly": f"{backup_config.monthly_retention_months} months"
            },
            "completed_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

# Disaster Recovery Endpoints

@router.get("/disaster-recovery/status")
async def get_disaster_recovery_status():
    """Get disaster recovery system status"""
    
    return await disaster_recovery.get_recovery_status()

@router.post("/disaster-recovery/health-check")
async def run_health_checks():
    """Run comprehensive system health checks"""
    
    health_status = await disaster_recovery.health_monitor.run_health_checks()
    
    # Check for potential disasters
    potential_disaster = await disaster_recovery.detect_disaster(health_status)
    
    return {
        "health_status": health_status,
        "potential_disaster": potential_disaster.value if potential_disaster else None,
        "disaster_scenarios_available": len(disaster_recovery.recovery_scenarios),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/disaster-recovery/execute")
async def execute_disaster_recovery(
    disaster_type: str,
    manual_override: bool = Query(False, description="Override automatic response restrictions"),
    confirm: bool = Query(False, description="Confirmation required for recovery execution")
):
    """Execute disaster recovery procedure"""
    
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Disaster recovery execution requires explicit confirmation. Set confirm=true"
        )
    
    try:
        # Convert string to enum
        disaster_enum = DisasterType(disaster_type)
    except ValueError:
        valid_types = [dt.value for dt in DisasterType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid disaster type. Valid types: {valid_types}"
        )
    
    try:
        result = await disaster_recovery.execute_recovery(disaster_enum, manual_override)
        
        if result["success"]:
            return {
                "message": "Disaster recovery executed successfully",
                "recovery_id": result["recovery_id"],
                "disaster_type": disaster_type,
                "duration_minutes": result.get("duration_minutes", 0),
                "steps_completed": len(result.get("steps_completed", [])),
                "completed_at": datetime.now().isoformat()
            }
        else:
            return {
                "message": "Disaster recovery execution completed with errors",
                "recovery_id": result["recovery_id"],
                "errors": result.get("errors", []),
                "steps_completed": len(result.get("steps_completed", [])),
                "completed_at": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recovery execution failed: {str(e)}")

@router.get("/disaster-recovery/scenarios")
async def list_disaster_scenarios():
    """List available disaster recovery scenarios"""
    
    scenarios = []
    for disaster_type, scenario in disaster_recovery.recovery_scenarios.items():
        scenarios.append({
            "disaster_type": disaster_type.value,
            "priority": scenario.priority.value,
            "rto_minutes": scenario.rto_minutes,
            "rpo_minutes": scenario.rpo_minutes,
            "automated_response": scenario.automated_response,
            "dependencies": scenario.dependencies,
            "success_criteria": scenario.success_criteria
        })
    
    return {
        "scenarios": scenarios,
        "total_scenarios": len(scenarios)
    }

# Business Continuity Endpoints

@router.get("/business-continuity/status")
async def get_business_continuity_status():
    """Get business continuity system status"""
    
    return business_continuity.get_continuity_status()

@router.get("/business-continuity/functions")
async def list_business_functions():
    """List critical business functions"""
    
    functions = []
    for func_name, function in business_continuity.business_functions.items():
        functions.append({
            "name": func_name,
            "description": function.description,
            "impact_level": function.impact_level.value,
            "recovery_strategy": function.recovery_strategy.value,
            "max_downtime_minutes": function.sla_requirements["max_downtime_minutes"],
            "stakeholders": function.stakeholders,
            "dependencies": function.dependencies
        })
    
    return {
        "functions": functions,
        "total_functions": len(functions)
    }

@router.post("/business-continuity/activate")
async def activate_continuity_plan(
    function_name: str,
    incident_description: str,
    severity: str = Query("medium", description="Incident severity: low, medium, high, critical"),
    confirm: bool = Query(False, description="Confirmation required for plan activation")
):
    """Activate business continuity plan for a function"""
    
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Business continuity plan activation requires explicit confirmation. Set confirm=true"
        )
    
    if function_name not in business_continuity.business_functions:
        available_functions = list(business_continuity.business_functions.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unknown business function. Available functions: {available_functions}"
        )
    
    incident_details = {
        "description": incident_description,
        "severity": severity,
        "reported_at": datetime.now().isoformat(),
        "reported_by": "api"  # Would include actual user info
    }
    
    try:
        result = await business_continuity.activate_continuity_plan(function_name, incident_details)
        
        if result["success"]:
            return {
                "message": "Business continuity plan activated successfully",
                "activation_id": result["activation_id"],
                "function_name": function_name,
                "actions_completed": len(result.get("actions_completed", [])),
                "notifications_sent": len(result.get("notifications_sent", [])),
                "status": result["status"]
            }
        else:
            return {
                "message": "Business continuity plan activation failed",
                "activation_id": result["activation_id"],
                "error": result.get("error", "Unknown error"),
                "status": result["status"]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan activation failed: {str(e)}")

@router.post("/business-continuity/test")
async def test_continuity_plan(
    function_name: str,
    test_type: str = Query("tabletop", description="Test type: tabletop, simulation")
):
    """Test business continuity plan"""
    
    if function_name not in business_continuity.business_functions:
        available_functions = list(business_continuity.business_functions.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unknown business function. Available functions: {available_functions}"
        )
    
    if test_type not in ["tabletop", "simulation"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid test type. Valid types: tabletop, simulation"
        )
    
    try:
        result = await business_continuity.test_continuity_plan(function_name, test_type)
        
        return {
            "message": "Business continuity plan test completed",
            "test_id": result["test_id"],
            "function_name": function_name,
            "test_type": test_type,
            "success": result["success"],
            "test_scenarios": result.get("test_scenarios", []),
            "completed_at": result.get("completed_at")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan test failed: {str(e)}")

@router.get("/business-continuity/incidents")
async def list_active_incidents():
    """List active business continuity incidents"""
    
    incidents = []
    for incident_id, incident_data in business_continuity.active_incidents.items():
        incidents.append({
            "incident_id": incident_id,
            "function_name": incident_data["function_name"],
            "status": incident_data["status"],
            "started_at": incident_data["started_at"],
            "actions_completed": len(incident_data.get("actions_completed", [])),
            "success": incident_data.get("success", False)
        })
    
    return {
        "active_incidents": incidents,
        "total_incidents": len(incidents)
    }

# Comprehensive System Status

@router.get("/system/status")
async def get_comprehensive_status():
    """Get comprehensive backup, recovery, and continuity status"""
    
    # Gather all status information
    backup_status = backup_manager.get_backup_status()
    disaster_recovery_status = await disaster_recovery.get_recovery_status()
    business_continuity_status = business_continuity.get_continuity_status()
    
    # Determine overall system readiness
    overall_status = "ready"
    issues = []
    
    # Check backup health
    if not backup_status.get("last_backup"):
        overall_status = "warning"
        issues.append("No recent backup found")
    
    # Check system health
    if disaster_recovery_status["system_health"]["overall_status"] != "healthy":
        overall_status = "warning"
        issues.append("System health issues detected")
    
    # Check business continuity readiness
    if business_continuity_status["overall_readiness"] != "ready":
        overall_status = "warning"
        issues.append(f"Business continuity: {business_continuity_status['overall_readiness']}")
    
    # Check for active incidents
    if disaster_recovery_status.get("potential_disaster"):
        overall_status = "alert"
        issues.append(f"Potential disaster detected: {disaster_recovery_status['potential_disaster']}")
    
    if business_continuity_status["active_incidents"] > 0:
        overall_status = "incident"
        issues.append(f"{business_continuity_status['active_incidents']} active incidents")
    
    return {
        "overall_status": overall_status,
        "issues": issues,
        "timestamp": datetime.now().isoformat(),
        "backup_system": {
            "status": "healthy" if backup_status.get("last_backup") else "warning",
            "last_backup": backup_status.get("last_backup", {}).get("created_at"),
            "backup_count": backup_status.get("backup_count", 0),
            "storage_locations": backup_status.get("storage_locations", [])
        },
        "disaster_recovery": {
            "status": disaster_recovery_status["system_health"]["overall_status"],
            "scenarios_available": len(disaster_recovery.recovery_scenarios),
            "potential_disaster": disaster_recovery_status.get("potential_disaster"),
            "last_recovery": disaster_recovery_status.get("last_recovery")
        },
        "business_continuity": {
            "status": business_continuity_status["overall_readiness"],
            "functions_covered": business_continuity_status["business_functions"],
            "active_incidents": business_continuity_status["active_incidents"],
            "testing_overdue": sum(1 for func_status in business_continuity_status["functions_status"].values() 
                                if func_status["testing_overdue"])
        }
    }

# Emergency Endpoints

@router.post("/emergency/full-recovery")
async def emergency_full_recovery(
    restore_from_backup: bool = Query(True, description="Whether to restore from latest backup"),
    emergency_code: str = Query(..., description="Emergency authorization code"),
    confirm_data_loss: bool = Query(False, description="Acknowledge potential data loss")
):
    """Emergency full system recovery procedure"""
    
    # Validate emergency code (in production, this would be a secure token)
    if emergency_code != "EMERGENCY_DOMUS_2025":
        raise HTTPException(status_code=403, detail="Invalid emergency authorization code")
    
    if not confirm_data_loss:
        raise HTTPException(
            status_code=400,
            detail="Emergency recovery may result in data loss. Set confirm_data_loss=true to proceed"
        )
    
    recovery_log = {
        "started_at": datetime.now().isoformat(),
        "emergency_code_used": True,
        "restore_from_backup": restore_from_backup,
        "steps": []
    }
    
    try:
        # Step 1: Execute disaster recovery for complete system failure
        recovery_log["steps"].append("Executing disaster recovery for complete system failure")
        disaster_result = await disaster_recovery.execute_recovery(
            DisasterType.COMPLETE_SYSTEM_FAILURE, 
            manual_override=True
        )
        
        # Step 2: Restore from backup if requested
        if restore_from_backup:
            recovery_log["steps"].append("Restoring from latest backup")
            backup_status = backup_manager.get_backup_status()
            if backup_status.get("last_backup"):
                backup_id = backup_status["last_backup"]["backup_id"]
                restore_result = backup_manager.restore_backup(backup_id)
                recovery_log["backup_restore"] = restore_result
            else:
                recovery_log["steps"].append("No backup available for restoration")
        
        # Step 3: Activate all critical business continuity plans
        recovery_log["steps"].append("Activating critical business continuity plans")
        critical_functions = [
            name for name, func in business_continuity.business_functions.items()
            if func.impact_level.value == "severe"
        ]
        
        for func_name in critical_functions:
            await business_continuity.activate_continuity_plan(func_name, {
                "description": "Emergency full recovery activation",
                "severity": "critical",
                "reported_at": datetime.now().isoformat(),
                "reported_by": "emergency_recovery"
            })
        
        recovery_log["completed_at"] = datetime.now().isoformat()
        recovery_log["success"] = True
        
        return {
            "message": "Emergency full recovery initiated",
            "recovery_log": recovery_log,
            "next_steps": [
                "Monitor system health continuously",
                "Validate all critical functions",
                "Notify all stakeholders of recovery status",
                "Conduct post-incident review"
            ]
        }
        
    except Exception as e:
        recovery_log["error"] = str(e)
        recovery_log["completed_at"] = datetime.now().isoformat()
        recovery_log["success"] = False
        
        raise HTTPException(
            status_code=500, 
            detail=f"Emergency recovery failed: {str(e)}"
        )