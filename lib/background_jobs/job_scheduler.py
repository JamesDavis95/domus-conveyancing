"""
Background Job Scheduler with Celery
Handles scheduled tasks for RAG refresh, LPA data updates, usage resets, and monitoring
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from celery import Celery, Task
from celery.schedules import crontab
import redis
import requests
import json
from dataclasses import dataclass
from enum import Enum

from .alert_system import AlertSystem, AlertLevel, AlertChannel
from ..database import get_db_connection
from ..rag.knowledge_refresh import KnowledgeRefreshService
from ..lpa.data_updater import LPADataUpdater
from ..monitoring.metrics import MetricsCollector
from ..billing.usage_tracker import UsageTracker

# Celery app configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

# Create Celery app
celery_app = Celery(
    'domus_background_jobs',
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=[
        'lib.background_jobs.job_scheduler',
        'lib.background_jobs.rag_refresh_jobs',
        'lib.background_jobs.lpa_update_jobs',
        'lib.background_jobs.monitoring_jobs'
    ]
)

# Celery configuration
celery_app.conf.update(
    timezone='Europe/London',
    enable_utc=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    result_expires=3600,
    task_routes={
        'lib.background_jobs.rag_refresh_jobs.*': {'queue': 'rag_queue'},
        'lib.background_jobs.lpa_update_jobs.*': {'queue': 'lpa_queue'},
        'lib.background_jobs.monitoring_jobs.*': {'queue': 'monitoring_queue'},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=100,
)

# Schedule configuration
celery_app.conf.beat_schedule = {
    # RAG Knowledge Refresh - Every 6 hours
    'refresh-rag-knowledge': {
        'task': 'lib.background_jobs.rag_refresh_jobs.refresh_knowledge_base',
        'schedule': crontab(minute=0, hour='*/6'),
        'options': {'queue': 'rag_queue'}
    },
    
    # LPA Data Updates - Daily at 3 AM
    'update-lpa-data': {
        'task': 'lib.background_jobs.lpa_update_jobs.update_all_lpa_data',
        'schedule': crontab(minute=0, hour=3),
        'options': {'queue': 'lpa_queue'}
    },
    
    # Appeals and Objections Ingestion - Every 4 hours
    'ingest-appeals-objections': {
        'task': 'lib.background_jobs.lpa_update_jobs.ingest_appeals_objections',
        'schedule': crontab(minute=30, hour='*/4'),
        'options': {'queue': 'lpa_queue'}
    },
    
    # Usage Resets - Daily at midnight
    'reset-daily-usage': {
        'task': 'lib.background_jobs.monitoring_jobs.reset_daily_usage',
        'schedule': crontab(minute=0, hour=0),
        'options': {'queue': 'monitoring_queue'}
    },
    
    # Freshness Tracking - Every 2 hours
    'track-data-freshness': {
        'task': 'lib.background_jobs.monitoring_jobs.track_data_freshness',
        'schedule': crontab(minute=0, hour='*/2'),
        'options': {'queue': 'monitoring_queue'}
    },
    
    # System Health Monitoring - Every 15 minutes
    'monitor-system-health': {
        'task': 'lib.background_jobs.monitoring_jobs.monitor_system_health',
        'schedule': crontab(minute='*/15'),
        'options': {'queue': 'monitoring_queue'}
    },
    
    # Database Cleanup - Daily at 2 AM
    'cleanup-old-data': {
        'task': 'lib.background_jobs.monitoring_jobs.cleanup_old_data',
        'schedule': crontab(minute=0, hour=2),
        'options': {'queue': 'monitoring_queue'}
    },
    
    # Backup Verification - Daily at 4 AM
    'verify-backups': {
        'task': 'lib.background_jobs.monitoring_jobs.verify_backup_integrity',
        'schedule': crontab(minute=0, hour=4),
        'options': {'queue': 'monitoring_queue'}
    },
    
    # Performance Metrics Collection - Every 5 minutes
    'collect-performance-metrics': {
        'task': 'lib.background_jobs.monitoring_jobs.collect_performance_metrics',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'monitoring_queue'}
    },
    
    # Weekly Reports - Sundays at 8 AM
    'generate-weekly-reports': {
        'task': 'lib.background_jobs.monitoring_jobs.generate_weekly_reports',
        'schedule': crontab(minute=0, hour=8, day_of_week=0),
        'options': {'queue': 'monitoring_queue'}
    }
}

# Job status tracking
class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"

@dataclass
class JobResult:
    job_id: str
    task_name: str
    status: JobStatus
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    retry_count: int

class DomusTask(Task):
    """Custom Celery task class with enhanced monitoring and alerting"""
    
    def __init__(self):
        self.alert_system = AlertSystem()
        self.metrics_collector = MetricsCollector()
        
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logging.info(f"Task {self.name} ({task_id}) completed successfully")
        
        # Record success metrics
        self.metrics_collector.record_job_completion(
            job_name=self.name,
            status=JobStatus.SUCCESS,
            duration=getattr(self.request, 'duration', None)
        )
        
        # Send success notification for critical jobs
        if self._is_critical_job():
            self.alert_system.send_alert(
                title=f"✅ Critical Job Completed: {self.name}",
                message=f"Job {task_id} completed successfully",
                level=AlertLevel.INFO,
                channels=[AlertChannel.SLACK]
            )
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logging.error(f"Task {self.name} ({task_id}) failed: {exc}")
        
        # Record failure metrics
        self.metrics_collector.record_job_completion(
            job_name=self.name,
            status=JobStatus.FAILURE,
            error=str(exc)
        )
        
        # Send failure alert
        self.alert_system.send_alert(
            title=f"❌ Job Failed: {self.name}",
            message=f"Job {task_id} failed with error: {exc}",
            level=AlertLevel.ERROR,
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            metadata={
                'task_id': task_id,
                'error': str(exc),
                'traceback': einfo.traceback
            }
        )
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logging.warning(f"Task {self.name} ({task_id}) being retried: {exc}")
        
        # Record retry metrics
        self.metrics_collector.record_job_retry(
            job_name=self.name,
            retry_count=self.request.retries
        )
        
        # Send retry alert for multiple retries
        if self.request.retries > 2:
            self.alert_system.send_alert(
                title=f"⚠️ Job Retrying: {self.name}",
                message=f"Job {task_id} on retry #{self.request.retries}: {exc}",
                level=AlertLevel.WARNING,
                channels=[AlertChannel.SLACK]
            )
    
    def _is_critical_job(self) -> bool:
        """Check if this is a critical job that needs special monitoring"""
        critical_jobs = [
            'update_all_lpa_data',
            'refresh_knowledge_base',
            'verify_backup_integrity',
            'monitor_system_health'
        ]
        return any(critical in self.name for critical in critical_jobs)

# Set custom task class
celery_app.Task = DomusTask

class JobScheduler:
    """Central job scheduler for managing background tasks"""
    
    def __init__(self):
        self.redis_client = redis.from_url(REDIS_URL)
        self.alert_system = AlertSystem()
        self.logger = logging.getLogger(__name__)
        
    def schedule_immediate_job(self, task_name: str, *args, **kwargs) -> str:
        """Schedule an immediate job execution"""
        try:
            result = celery_app.send_task(task_name, args=args, kwargs=kwargs)
            
            self.logger.info(f"Scheduled immediate job: {task_name} ({result.id})")
            
            # Store job metadata
            self._store_job_metadata(result.id, task_name, 'immediate')
            
            return result.id
            
        except Exception as e:
            self.logger.error(f"Failed to schedule job {task_name}: {e}")
            self.alert_system.send_alert(
                title="❌ Job Scheduling Failed",
                message=f"Failed to schedule {task_name}: {e}",
                level=AlertLevel.ERROR,
                channels=[AlertChannel.SLACK]
            )
            raise
    
    def schedule_delayed_job(self, task_name: str, delay_seconds: int, *args, **kwargs) -> str:
        """Schedule a job with delay"""
        try:
            eta = datetime.utcnow() + timedelta(seconds=delay_seconds)
            result = celery_app.send_task(task_name, args=args, kwargs=kwargs, eta=eta)
            
            self.logger.info(f"Scheduled delayed job: {task_name} ({result.id}) - ETA: {eta}")
            
            # Store job metadata
            self._store_job_metadata(result.id, task_name, 'delayed', eta=eta)
            
            return result.id
            
        except Exception as e:
            self.logger.error(f"Failed to schedule delayed job {task_name}: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[JobResult]:
        """Get status of a specific job"""
        try:
            result = celery_app.AsyncResult(job_id)
            
            # Get stored metadata
            metadata = self._get_job_metadata(job_id)
            
            return JobResult(
                job_id=job_id,
                task_name=metadata.get('task_name', 'unknown'),
                status=JobStatus(result.status.lower() if result.status else 'pending'),
                started_at=metadata.get('started_at'),
                completed_at=metadata.get('completed_at'),
                duration_seconds=metadata.get('duration'),
                result_data=result.result if result.successful() else None,
                error_message=str(result.result) if result.failed() else None,
                retry_count=metadata.get('retry_count', 0)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get job status for {job_id}: {e}")
            return None
    
    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get list of currently active jobs"""
        try:
            # Get active workers
            inspect = celery_app.control.inspect()
            
            active_jobs = []
            
            # Get active tasks from all workers
            active_tasks = inspect.active()
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    for task in tasks:
                        active_jobs.append({
                            'job_id': task['id'],
                            'task_name': task['name'],
                            'worker': worker,
                            'started_at': datetime.fromtimestamp(task['time_start']),
                            'args': task['args'],
                            'kwargs': task['kwargs']
                        })
            
            return active_jobs
            
        except Exception as e:
            self.logger.error(f"Failed to get active jobs: {e}")
            return []
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled or running job"""
        try:
            celery_app.control.revoke(job_id, terminate=True)
            
            self.logger.info(f"Cancelled job: {job_id}")
            
            # Update job metadata
            self._update_job_metadata(job_id, {'cancelled_at': datetime.utcnow()})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    def get_job_history(self, limit: int = 100) -> List[JobResult]:
        """Get recent job history"""
        try:
            # Get job history from Redis
            job_keys = self.redis_client.keys('job_metadata:*')
            jobs = []
            
            for key in job_keys[-limit:]:
                job_id = key.decode().split(':')[1]
                job_result = self.get_job_status(job_id)
                if job_result:
                    jobs.append(job_result)
            
            # Sort by start time (newest first)
            jobs.sort(key=lambda x: x.started_at or datetime.min, reverse=True)
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Failed to get job history: {e}")
            return []
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get job execution statistics"""
        try:
            # Get statistics from Redis
            stats = {
                'total_jobs': 0,
                'successful_jobs': 0,
                'failed_jobs': 0,
                'jobs_by_type': {},
                'average_duration': 0,
                'last_24h_jobs': 0
            }
            
            job_keys = self.redis_client.keys('job_metadata:*')
            total_duration = 0
            duration_count = 0
            
            for key in job_keys:
                metadata = json.loads(self.redis_client.get(key) or '{}')
                stats['total_jobs'] += 1
                
                # Count by status
                status = metadata.get('status', 'unknown')
                if status == 'SUCCESS':
                    stats['successful_jobs'] += 1
                elif status == 'FAILURE':
                    stats['failed_jobs'] += 1
                
                # Count by type
                task_name = metadata.get('task_name', 'unknown')
                stats['jobs_by_type'][task_name] = stats['jobs_by_type'].get(task_name, 0) + 1
                
                # Calculate average duration
                if metadata.get('duration'):
                    total_duration += metadata['duration']
                    duration_count += 1
                
                # Count last 24h jobs
                started_at = metadata.get('started_at')
                if started_at:
                    start_time = datetime.fromisoformat(started_at)
                    if start_time > datetime.utcnow() - timedelta(hours=24):
                        stats['last_24h_jobs'] += 1
            
            if duration_count > 0:
                stats['average_duration'] = total_duration / duration_count
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get job statistics: {e}")
            return {}
    
    def _store_job_metadata(self, job_id: str, task_name: str, schedule_type: str, **kwargs):
        """Store job metadata in Redis"""
        metadata = {
            'task_name': task_name,
            'schedule_type': schedule_type,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'PENDING',
            **kwargs
        }
        
        # Convert datetime objects to ISO format
        for key, value in metadata.items():
            if isinstance(value, datetime):
                metadata[key] = value.isoformat()
        
        self.redis_client.setex(
            f'job_metadata:{job_id}',
            timedelta(days=7),  # Keep metadata for 7 days
            json.dumps(metadata)
        )
    
    def _get_job_metadata(self, job_id: str) -> Dict[str, Any]:
        """Get job metadata from Redis"""
        try:
            data = self.redis_client.get(f'job_metadata:{job_id}')
            if data:
                metadata = json.loads(data)
                
                # Convert ISO dates back to datetime
                for key in ['created_at', 'started_at', 'completed_at', 'eta']:
                    if key in metadata and metadata[key]:
                        metadata[key] = datetime.fromisoformat(metadata[key])
                
                return metadata
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get job metadata for {job_id}: {e}")
            return {}
    
    def _update_job_metadata(self, job_id: str, updates: Dict[str, Any]):
        """Update job metadata in Redis"""
        try:
            metadata = self._get_job_metadata(job_id)
            metadata.update(updates)
            
            # Convert datetime objects to ISO format
            for key, value in metadata.items():
                if isinstance(value, datetime):
                    metadata[key] = value.isoformat()
            
            self.redis_client.setex(
                f'job_metadata:{job_id}',
                timedelta(days=7),
                json.dumps(metadata)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update job metadata for {job_id}: {e}")

# Global job scheduler instance
job_scheduler = JobScheduler()

# Health check functions
def check_celery_workers() -> Dict[str, Any]:
    """Check if Celery workers are running"""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if not stats:
            return {
                'status': 'unhealthy',
                'message': 'No active Celery workers found',
                'workers': 0
            }
        
        worker_count = len(stats)
        return {
            'status': 'healthy',
            'message': f'{worker_count} active workers',
            'workers': worker_count,
            'worker_details': stats
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Failed to check workers: {e}',
            'workers': 0
        }

def check_redis_connection() -> Dict[str, Any]:
    """Check Redis connection for job queue"""
    try:
        redis_client = redis.from_url(REDIS_URL)
        redis_client.ping()
        
        return {
            'status': 'healthy',
            'message': 'Redis connection successful'
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Redis connection failed: {e}'
        }

def get_queue_sizes() -> Dict[str, int]:
    """Get current queue sizes"""
    try:
        redis_client = redis.from_url(REDIS_URL)
        
        queues = ['rag_queue', 'lpa_queue', 'monitoring_queue', 'celery']
        queue_sizes = {}
        
        for queue in queues:
            queue_sizes[queue] = redis_client.llen(queue)
        
        return queue_sizes
        
    except Exception as e:
        logging.error(f"Failed to get queue sizes: {e}")
        return {}