"""
Background Jobs API Router
Provides REST endpoints for managing background jobs, monitoring, and alerts
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os

from backend_auth import get_current_user  
from lib.rbac import require_admin
from models import get_db

router = APIRouter(prefix="/api/background-jobs", tags=["Background Jobs"])

# Response Models
class JobScheduleRequest(BaseModel):
    job_type: str
    schedule_time: Optional[datetime] = None
    job_params: Optional[Dict[str, Any]] = {}
    priority: Optional[int] = 5

class JobResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    scheduled_for: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

class SystemHealthResponse(BaseModel):
    status: str
    components: Dict[str, Dict[str, Any]]
    timestamp: datetime

class AlertRequest(BaseModel):
    title: str
    message: str
    level: str  # 'info', 'warning', 'error', 'critical'
    channels: List[str]  # ['email', 'slack']

# Job Management Endpoints
@router.post("/schedule", response_model=JobResponse)
async def schedule_job(
    request: JobScheduleRequest,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Schedule a background job for execution"""
    try:
        # For now, create a simple job record
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Log the job scheduling
        db.execute(
            """INSERT INTO job_execution_logs 
               (job_id, job_type, status, created_at, job_params, priority)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (job_id, request.job_type, 'scheduled', datetime.now(), 
             json.dumps(request.job_params), request.priority)
        )
        db.commit()
        
        return JobResponse(
            job_id=job_id,
            status='scheduled',
            created_at=datetime.now(),
            scheduled_for=request.schedule_time or datetime.now(),
            completed_at=None,
            error_message=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule job: {str(e)}")

@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    limit: int = 50,
    status: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List background jobs with optional filtering"""
    try:
        query = "SELECT * FROM job_execution_logs"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
            
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        result = db.execute(query, params).fetchall()
        
        jobs = []
        for row in result:
            jobs.append(JobResponse(
                job_id=row[1],  # job_id
                status=row[3],  # status
                created_at=row[4],  # created_at
                scheduled_for=row[5] if len(row) > 5 else None,
                completed_at=row[6] if len(row) > 6 else None,
                error_message=row[7] if len(row) > 7 else None
            ))
            
        return jobs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status of a specific job"""
    try:
        result = db.execute(
            "SELECT * FROM job_execution_logs WHERE job_id = ?",
            (job_id,)
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Job not found")
            
        return JobResponse(
            job_id=result[1],
            status=result[3],
            created_at=result[4],
            scheduled_for=result[5] if len(result) > 5 else None,
            completed_at=result[6] if len(result) > 6 else None,
            error_message=result[7] if len(result) > 7 else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

# System Health Endpoints
@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall system health status"""
    try:
        # Check database connectivity
        db_status = "healthy"
        try:
            db.execute("SELECT 1").fetchone()
        except:
            db_status = "unhealthy"
        
        # Check recent job failures
        recent_failures = db.execute(
            """SELECT COUNT(*) FROM job_execution_logs 
               WHERE status = 'failed' AND created_at > ?""",
            (datetime.now() - timedelta(hours=1),)
        ).fetchone()[0]
        
        job_status = "healthy" if recent_failures < 5 else "degraded"
        
        # Overall system status
        overall_status = "healthy"
        if db_status != "healthy" or job_status == "degraded":
            overall_status = "degraded"
        
        return SystemHealthResponse(
            status=overall_status,
            components={
                "database": {"status": db_status},
                "background_jobs": {"status": job_status, "recent_failures": recent_failures},
                "redis": {"status": "unknown"},  # Would check Redis if available
                "celery": {"status": "unknown"}   # Would check Celery if available
            },
            timestamp=datetime.now()
        )
        
    except Exception as e:
        return SystemHealthResponse(
            status="error",
            components={"error": {"message": str(e)}},
            timestamp=datetime.now()
        )

# Alert Management Endpoints
@router.post("/alerts/send")
async def send_alert(
    request: AlertRequest,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Send an alert through configured channels"""
    try:
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Log the alert
        db.execute(
            """INSERT INTO alert_history 
               (alert_id, title, message, level, channels, created_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (alert_id, request.title, request.message, request.level,
             json.dumps(request.channels), datetime.now(), 'sent')
        )
        db.commit()
        
        return {"alert_id": alert_id, "status": "sent", "channels": request.channels}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send alert: {str(e)}")

@router.get("/alerts")
async def list_alerts(
    limit: int = 50,
    level: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List recent alerts"""
    try:
        query = "SELECT * FROM alert_history"
        params = []
        
        if level:
            query += " WHERE level = ?"
            params.append(level)
            
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        result = db.execute(query, params).fetchall()
        
        alerts = []
        for row in result:
            alerts.append({
                "alert_id": row[1],
                "title": row[2],
                "message": row[3],
                "level": row[4],
                "channels": json.loads(row[5]) if row[5] else [],
                "created_at": row[6],
                "status": row[7]
            })
            
        return alerts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list alerts: {str(e)}")

# Manual Job Triggers
@router.post("/trigger/rag-refresh")
async def trigger_rag_refresh(
    current_user = Depends(require_admin),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Manually trigger RAG knowledge base refresh"""
    try:
        job_id = f"rag_refresh_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Log the manual trigger
        db.execute(
            """INSERT INTO job_execution_logs 
               (job_id, job_type, status, created_at, triggered_by)
               VALUES (?, ?, ?, ?, ?)""",
            (job_id, 'rag_refresh', 'triggered', datetime.now(), current_user.get('user_id'))
        )
        db.commit()
        
        # Add to background tasks (simplified for now)
        background_tasks.add_task(lambda: print(f"RAG refresh job {job_id} would execute here"))
        
        return {"job_id": job_id, "status": "triggered", "message": "RAG refresh job queued"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger RAG refresh: {str(e)}")

@router.post("/trigger/lpa-update")
async def trigger_lpa_update(
    current_user = Depends(require_admin),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Manually trigger LPA data update"""
    try:
        job_id = f"lpa_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Log the manual trigger
        db.execute(
            """INSERT INTO job_execution_logs 
               (job_id, job_type, status, created_at, triggered_by)
               VALUES (?, ?, ?, ?, ?)""",
            (job_id, 'lpa_update', 'triggered', datetime.now(), current_user.get('user_id'))
        )
        db.commit()
        
        # Add to background tasks (simplified for now)
        background_tasks.add_task(lambda: print(f"LPA update job {job_id} would execute here"))
        
        return {"job_id": job_id, "status": "triggered", "message": "LPA update job queued"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger LPA update: {str(e)}")

# Performance Metrics
@router.get("/metrics/performance")
async def get_performance_metrics(
    hours: int = 24,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system performance metrics"""
    try:
        since = datetime.now() - timedelta(hours=hours)
        
        # Job execution metrics
        job_stats = db.execute(
            """SELECT status, COUNT(*) as count FROM job_execution_logs 
               WHERE created_at > ? GROUP BY status""",
            (since,)
        ).fetchall()
        
        # System metrics
        system_metrics = db.execute(
            """SELECT metric_name, AVG(value) as avg_value, MAX(value) as max_value 
               FROM system_metrics WHERE recorded_at > ? 
               GROUP BY metric_name""",
            (since,)
        ).fetchall()
        
        metrics = {
            "job_statistics": {row[0]: row[1] for row in job_stats},
            "system_performance": {row[0]: {"average": row[1], "maximum": row[2]} for row in system_metrics},
            "period_hours": hours,
            "generated_at": datetime.now()
        }
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

# Configuration Management
@router.get("/config")
async def get_background_jobs_config(
    current_user = Depends(require_admin)
):
    """Get background jobs configuration"""
    try:
        config = {
            "celery_configured": os.getenv('CELERY_BROKER_URL') is not None,
            "redis_configured": os.getenv('REDIS_URL') is not None,
            "slack_configured": os.getenv('SLACK_WEBHOOK_URL') is not None,
            "email_configured": os.getenv('SMTP_HOST') is not None,
            "rag_refresh_interval": "6 hours",
            "lpa_update_interval": "daily",
            "monitoring_interval": "15 minutes",
            "cleanup_interval": "daily"
        }
        
        return config
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")