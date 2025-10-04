"""
Celery configuration for Domus Background Jobs
Configures Celery worker and beat scheduler for production deployment
"""

import os
from celery import Celery
from datetime import timedelta

# Environment configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

# Create Celery app
app = Celery('domus_background_jobs')

# Basic configuration
app.conf.update(
    # Broker settings
    broker_url=BROKER_URL,
    result_backend=RESULT_BACKEND,
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/London',
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    worker_disable_rate_limits=False,
    
    # Results settings
    result_expires=3600,  # 1 hour
    result_compression='gzip',
    
    # Route tasks to specific queues
    task_routes={
        'lib.background_jobs.rag_refresh_jobs.*': {'queue': 'rag_queue'},
        'lib.background_jobs.lpa_update_jobs.*': {'queue': 'lpa_queue'},
        'lib.background_jobs.monitoring_jobs.*': {'queue': 'monitoring_queue'},
    },
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # RAG Knowledge Refresh - Every 6 hours
    'refresh-rag-knowledge': {
        'task': 'lib.background_jobs.rag_refresh_jobs.refresh_knowledge_base',
        'schedule': timedelta(hours=6),
        'options': {'queue': 'rag_queue', 'priority': 5}
    },
    
    # LPA Data Updates - Daily at 3 AM
    'update-lpa-data': {
        'task': 'lib.background_jobs.lpa_update_jobs.update_all_lpa_data',
        'schedule': timedelta(days=1),
        'options': {'queue': 'lpa_queue', 'priority': 7}
    },
    
    # Appeals and Objections Ingestion - Every 4 hours
    'ingest-appeals-objections': {
        'task': 'lib.background_jobs.lpa_update_jobs.ingest_appeals_objections',
        'schedule': timedelta(hours=4),
        'options': {'queue': 'lpa_queue', 'priority': 6}
    },
    
    # Usage Resets - Daily at midnight
    'reset-daily-usage': {
        'task': 'lib.background_jobs.monitoring_jobs.reset_daily_usage',
        'schedule': timedelta(days=1),
        'options': {'queue': 'monitoring_queue', 'priority': 8}
    },
    
    # Freshness Tracking - Every 2 hours
    'track-data-freshness': {
        'task': 'lib.background_jobs.monitoring_jobs.track_data_freshness',
        'schedule': timedelta(hours=2),
        'options': {'queue': 'monitoring_queue', 'priority': 4}
    },
    
    # System Health Monitoring - Every 15 minutes
    'monitor-system-health': {
        'task': 'lib.background_jobs.monitoring_jobs.monitor_system_health',
        'schedule': timedelta(minutes=15),
        'options': {'queue': 'monitoring_queue', 'priority': 3}
    },
    
    # Database Cleanup - Daily at 2 AM
    'cleanup-old-data': {
        'task': 'lib.background_jobs.monitoring_jobs.cleanup_old_data',
        'schedule': timedelta(days=1),
        'options': {'queue': 'monitoring_queue', 'priority': 2}
    },
    
    # Backup Verification - Daily at 4 AM
    'verify-backups': {
        'task': 'lib.background_jobs.monitoring_jobs.verify_backup_integrity',
        'schedule': timedelta(days=1),
        'options': {'queue': 'monitoring_queue', 'priority': 9}
    },
    
    # Performance Metrics Collection - Every 5 minutes
    'collect-performance-metrics': {
        'task': 'lib.background_jobs.monitoring_jobs.collect_performance_metrics',
        'schedule': timedelta(minutes=5),
        'options': {'queue': 'monitoring_queue', 'priority': 1}
    },
    
    # Weekly Reports - Sundays at 8 AM
    'generate-weekly-reports': {
        'task': 'lib.background_jobs.monitoring_jobs.generate_weekly_reports',
        'schedule': timedelta(weeks=1),
        'options': {'queue': 'monitoring_queue', 'priority': 6}
    }
}

# Include task modules
app.autodiscover_tasks([
    'lib.background_jobs.rag_refresh_jobs',
    'lib.background_jobs.lpa_update_jobs', 
    'lib.background_jobs.monitoring_jobs'
])

if __name__ == '__main__':
    app.start()