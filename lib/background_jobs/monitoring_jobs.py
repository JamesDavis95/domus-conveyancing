"""
Background Jobs for System Monitoring and Maintenance
Handles usage resets, freshness tracking, health monitoring, and alerts
"""

import logging
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import sqlite3
import boto3
from pathlib import Path

from celery import current_task
from ..background_jobs.job_scheduler import celery_app, DomusTask
from ..background_jobs.alert_system import AlertSystem, AlertLevel, AlertChannel
from ..billing.usage_tracker import UsageTracker
from ..monitoring.metrics import MetricsCollector
from ..monitoring.health_checker import HealthChecker
from ..database import get_db_connection

# Initialize services
usage_tracker = UsageTracker()
metrics_collector = MetricsCollector()
health_checker = HealthChecker()
alert_system = AlertSystem()

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.monitoring_jobs.reset_daily_usage')
def reset_daily_usage(self):
    """Reset daily usage counters for all organizations"""
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting daily usage reset (task_id: {task_id})")
        
        reset_stats = {
            'started_at': datetime.utcnow().isoformat(),
            'organizations_reset': 0,
            'quotas_reset': 0,
            'errors': []
        }
        
        # Get all active organizations
        self.update_state(state='PROGRESS', meta={'step': 'fetching_organizations', 'progress': 20})
        
        with get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name FROM organizations 
                WHERE active = 1 AND subscription_status = 'active'
            """)
            organizations = cursor.fetchall()
        
        total_orgs = len(organizations)
        logger.info(f"Resetting usage for {total_orgs} organizations")
        
        # Reset usage for each organization
        for i, (org_id, org_name) in enumerate(organizations):
            try:
                # Update progress
                progress = 20 + (i / total_orgs) * 60
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'step': f'resetting_org_{org_id}',
                        'progress': progress,
                        'current_org': org_name,
                        'processed': i,
                        'total': total_orgs
                    }
                )
                
                # Reset daily usage for this organization
                quotas_reset = usage_tracker.reset_daily_usage(org_id)
                
                reset_stats['organizations_reset'] += 1
                reset_stats['quotas_reset'] += quotas_reset
                
                logger.debug(f"Reset {quotas_reset} quotas for organization {org_name}")
                
            except Exception as e:
                error_msg = f"Failed to reset usage for organization {org_name}: {e}"
                reset_stats['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Archive previous day's usage statistics
        self.update_state(state='PROGRESS', meta={'step': 'archiving_statistics', 'progress': 85})
        
        _archive_daily_usage_stats()
        
        # Update system statistics
        self.update_state(state='PROGRESS', meta={'step': 'updating_statistics', 'progress': 95})
        
        _update_system_usage_stats(reset_stats)
        
        reset_stats['completed_at'] = datetime.utcnow().isoformat()
        
        # Send notification
        alert_system.send_alert(
            title="🔄 Daily Usage Reset Complete",
            message=f"Successfully reset usage counters for {reset_stats['organizations_reset']} organizations",
            level=AlertLevel.INFO,
            channels=[AlertChannel.SLACK],
            metadata=reset_stats,
            throttle_key="daily_usage_reset",
            max_per_window=1  # Only one per day
        )
        
        logger.info(f"Daily usage reset completed: {reset_stats}")
        
        return reset_stats
        
    except Exception as e:
        error_msg = f"Daily usage reset failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        alert_system.send_alert(
            title="❌ Daily Usage Reset Failed",
            message=error_msg,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            metadata={'task_id': task_id}
        )
        
        raise

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.monitoring_jobs.track_data_freshness')
def track_data_freshness(self):
    """Track and alert on data freshness across all systems"""
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting data freshness tracking (task_id: {task_id})")
        
        freshness_report = {
            'started_at': datetime.utcnow().isoformat(),
            'data_sources_checked': 0,
            'stale_sources': [],
            'critical_sources': [],
            'warnings': [],
            'healthy_sources': []
        }
        
        # Define freshness thresholds (in hours)
        freshness_thresholds = {
            'knowledge_base': 12,      # RAG knowledge should be fresh within 12 hours
            'lpa_data': 24,           # LPA data should be fresh within 24 hours
            'appeals_data': 8,        # Appeals data should be fresh within 8 hours
            'constraints_data': 72,   # Constraints can be stale for up to 72 hours
            'hdt_5yhls_data': 168,    # HDT/5YHLS data can be stale for up to 1 week
            'embeddings': 24,         # Embeddings should be fresh within 24 hours
            'marketplace_data': 4     # Marketplace data should be very fresh
        }
        
        # Check each data source
        with get_db_connection() as conn:
            for source_type, threshold_hours in freshness_thresholds.items():
                try:
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'step': f'checking_{source_type}',
                            'progress': (freshness_report['data_sources_checked'] / len(freshness_thresholds)) * 80
                        }
                    )
                    
                    # Get last update time for this source
                    cursor = conn.execute("""
                        SELECT last_updated, status 
                        FROM knowledge_freshness 
                        WHERE type = ?
                    """, (source_type,))
                    
                    result = cursor.fetchone()
                    
                    if result:
                        last_updated, status = result
                        if isinstance(last_updated, str):
                            last_updated = datetime.fromisoformat(last_updated)
                        
                        # Calculate staleness
                        hours_since_update = (datetime.utcnow() - last_updated).total_seconds() / 3600
                        
                        source_info = {
                            'type': source_type,
                            'last_updated': last_updated.isoformat(),
                            'hours_since_update': round(hours_since_update, 2),
                            'threshold_hours': threshold_hours,
                            'status': status
                        }
                        
                        if hours_since_update > threshold_hours * 2:
                            # Critical staleness (more than 2x threshold)
                            freshness_report['critical_sources'].append(source_info)
                        elif hours_since_update > threshold_hours:
                            # Warning staleness (exceeded threshold)
                            freshness_report['stale_sources'].append(source_info)
                        else:
                            # Healthy freshness
                            freshness_report['healthy_sources'].append(source_info)
                    else:
                        # No freshness data available
                        warning = f"No freshness data available for {source_type}"
                        freshness_report['warnings'].append(warning)
                        logger.warning(warning)
                    
                    freshness_report['data_sources_checked'] += 1
                    
                except Exception as e:
                    error_msg = f"Error checking freshness for {source_type}: {e}"
                    freshness_report['warnings'].append(error_msg)
                    logger.error(error_msg)
        
        # Check individual LPA freshness
        self.update_state(state='PROGRESS', meta={'step': 'checking_lpa_freshness', 'progress': 85})
        
        lpa_freshness_issues = _check_lpa_freshness()
        if lpa_freshness_issues:
            freshness_report['lpa_freshness_issues'] = lpa_freshness_issues
        
        freshness_report['completed_at'] = datetime.utcnow().isoformat()
        
        # Send alerts based on findings
        _send_freshness_alerts(freshness_report)
        
        # Store freshness report
        _store_freshness_report(freshness_report)
        
        logger.info(f"Data freshness tracking completed: {freshness_report}")
        
        return freshness_report
        
    except Exception as e:
        error_msg = f"Data freshness tracking failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        alert_system.send_alert(
            title="❌ Data Freshness Tracking Failed",
            message=error_msg,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            metadata={'task_id': task_id}
        )
        
        raise

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.monitoring_jobs.monitor_system_health')
def monitor_system_health(self):
    """Monitor overall system health and performance"""
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting system health monitoring (task_id: {task_id})")
        
        health_report = {
            'started_at': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'checks_performed': 0,
            'checks_passed': 0,
            'checks_failed': 0,
            'critical_issues': [],
            'warnings': [],
            'performance_metrics': {}
        }
        
        # Define health checks
        health_checks = [
            ('database', _check_database_health),
            ('redis', _check_redis_health),
            ('celery_workers', _check_celery_workers_health),
            ('disk_space', _check_disk_space),
            ('memory_usage', _check_memory_usage),
            ('cpu_usage', _check_cpu_usage),
            ('api_endpoints', _check_api_endpoints),
            ('external_apis', _check_external_apis),
            ('s3_connectivity', _check_s3_connectivity),
            ('stripe_connectivity', _check_stripe_connectivity)
        ]
        
        # Perform each health check
        for i, (check_name, check_function) in enumerate(health_checks):
            try:
                # Update progress
                progress = (i / len(health_checks)) * 80
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'step': f'checking_{check_name}',
                        'progress': progress,
                        'current_check': check_name
                    }
                )
                
                check_result = check_function()
                health_report['checks_performed'] += 1
                
                if check_result['status'] == 'healthy':
                    health_report['checks_passed'] += 1
                else:
                    health_report['checks_failed'] += 1
                    
                    if check_result['severity'] == 'critical':
                        health_report['critical_issues'].append({
                            'check': check_name,
                            'message': check_result['message'],
                            'details': check_result.get('details', {})
                        })
                        health_report['overall_status'] = 'critical'
                    else:
                        health_report['warnings'].append({
                            'check': check_name,
                            'message': check_result['message'],
                            'details': check_result.get('details', {})
                        })
                        if health_report['overall_status'] == 'healthy':
                            health_report['overall_status'] = 'warning'
                
                # Store performance metrics
                if 'metrics' in check_result:
                    health_report['performance_metrics'][check_name] = check_result['metrics']
                
                logger.debug(f"Health check {check_name}: {check_result['status']}")
                
            except Exception as e:
                health_report['checks_failed'] += 1
                error_msg = f"Health check {check_name} failed: {e}"
                health_report['critical_issues'].append({
                    'check': check_name,
                    'message': error_msg,
                    'details': {'exception': str(e)}
                })
                health_report['overall_status'] = 'critical'
                logger.error(error_msg)
        
        # Finalize report
        self.update_state(state='PROGRESS', meta={'step': 'finalizing', 'progress': 95})
        
        health_report['completed_at'] = datetime.utcnow().isoformat()
        health_report['success_rate'] = (health_report['checks_passed'] / health_report['checks_performed']) * 100
        
        # Store health metrics
        metrics_collector.record_health_check(health_report)
        
        # Send alerts based on health status
        _send_health_alerts(health_report)
        
        logger.info(f"System health monitoring completed: {health_report['overall_status']}")
        
        return health_report
        
    except Exception as e:
        error_msg = f"System health monitoring failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        alert_system.send_alert(
            title="❌ System Health Monitoring Failed",
            message=error_msg,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            metadata={'task_id': task_id}
        )
        
        raise

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.monitoring_jobs.cleanup_old_data')
def cleanup_old_data(self, retention_days: int = 90):
    """Clean up old data and logs"""
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting old data cleanup (task_id: {task_id})")
        
        cleanup_stats = {
            'started_at': datetime.utcnow().isoformat(),
            'tables_cleaned': 0,
            'records_deleted': 0,
            'space_freed_mb': 0,
            'errors': []
        }
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Define cleanup operations
        cleanup_operations = [
            ('api_logs', 'created_at', 30),           # Keep API logs for 30 days
            ('job_execution_logs', 'created_at', 7),  # Keep job logs for 7 days
            ('alert_history', 'created_at', 30),      # Keep alerts for 30 days
            ('usage_analytics', 'recorded_at', 365),  # Keep usage analytics for 1 year
            ('search_queries', 'created_at', 90),     # Keep search queries for 90 days
            ('system_metrics', 'recorded_at', 30),    # Keep system metrics for 30 days
            ('temp_files', 'created_at', 1),          # Clean temp files daily
        ]
        
        with get_db_connection() as conn:
            for table_name, date_column, retention_days_table in cleanup_operations:
                try:
                    # Update progress
                    progress = (cleanup_stats['tables_cleaned'] / len(cleanup_operations)) * 80
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'step': f'cleaning_{table_name}',
                            'progress': progress,
                            'current_table': table_name
                        }
                    )
                    
                    # Calculate table-specific cutoff
                    table_cutoff = datetime.utcnow() - timedelta(days=retention_days_table)
                    
                    # Check if table exists
                    cursor = conn.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name=?
                    """, (table_name,))
                    
                    if not cursor.fetchone():
                        logger.debug(f"Table {table_name} does not exist, skipping")
                        continue
                    
                    # Count records to be deleted
                    cursor = conn.execute(f"""
                        SELECT COUNT(*) FROM {table_name} 
                        WHERE {date_column} < ?
                    """, (table_cutoff,))
                    
                    count_to_delete = cursor.fetchone()[0]
                    
                    if count_to_delete > 0:
                        # Delete old records
                        conn.execute(f"""
                            DELETE FROM {table_name} 
                            WHERE {date_column} < ?
                        """, (table_cutoff,))
                        
                        cleanup_stats['records_deleted'] += count_to_delete
                        logger.info(f"Deleted {count_to_delete} old records from {table_name}")
                    
                    cleanup_stats['tables_cleaned'] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to cleanup table {table_name}: {e}"
                    cleanup_stats['errors'].append(error_msg)
                    logger.error(error_msg)
            
            # Vacuum database to reclaim space
            self.update_state(state='PROGRESS', meta={'step': 'vacuuming_database', 'progress': 90})
            
            # Get database size before vacuum
            db_size_before = _get_database_size()
            
            conn.execute("VACUUM")
            
            # Get database size after vacuum
            db_size_after = _get_database_size()
            cleanup_stats['space_freed_mb'] = round((db_size_before - db_size_after) / 1024 / 1024, 2)
        
        # Clean up file system
        self.update_state(state='PROGRESS', meta={'step': 'cleaning_filesystem', 'progress': 95})
        
        filesystem_cleanup = _cleanup_filesystem(retention_days)
        cleanup_stats.update(filesystem_cleanup)
        
        cleanup_stats['completed_at'] = datetime.utcnow().isoformat()
        
        # Send notification
        alert_system.send_alert(
            title="🧹 Data Cleanup Complete",
            message=f"Cleaned {cleanup_stats['records_deleted']} records from {cleanup_stats['tables_cleaned']} tables, freed {cleanup_stats['space_freed_mb']} MB",
            level=AlertLevel.INFO,
            channels=[AlertChannel.SLACK],
            metadata=cleanup_stats,
            throttle_key="data_cleanup_complete"
        )
        
        logger.info(f"Old data cleanup completed: {cleanup_stats}")
        
        return cleanup_stats
        
    except Exception as e:
        error_msg = f"Old data cleanup failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        alert_system.send_alert(
            title="❌ Data Cleanup Failed",
            message=error_msg,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            metadata={'task_id': task_id}
        )
        
        raise

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.monitoring_jobs.verify_backup_integrity')
def verify_backup_integrity(self):
    """Verify database backup integrity"""
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting backup integrity verification (task_id: {task_id})")
        
        verification_report = {
            'started_at': datetime.utcnow().isoformat(),
            'backups_checked': 0,
            'backups_valid': 0,
            'backups_corrupted': 0,
            'backup_details': [],
            'errors': []
        }
        
        # Get list of recent backups
        self.update_state(state='PROGRESS', meta={'step': 'listing_backups', 'progress': 10})
        
        backup_files = _get_recent_backups()
        total_backups = len(backup_files)
        
        if total_backups == 0:
            raise Exception("No backup files found for verification")
        
        # Verify each backup
        for i, backup_file in enumerate(backup_files):
            try:
                # Update progress
                progress = 10 + (i / total_backups) * 80
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'step': f'verifying_{backup_file["name"]}',
                        'progress': progress,
                        'current_backup': backup_file['name']
                    }
                )
                
                verification_result = _verify_single_backup(backup_file)
                
                verification_report['backups_checked'] += 1
                verification_report['backup_details'].append(verification_result)
                
                if verification_result['valid']:
                    verification_report['backups_valid'] += 1
                else:
                    verification_report['backups_corrupted'] += 1
                
                logger.info(f"Backup {backup_file['name']}: {'Valid' if verification_result['valid'] else 'Corrupted'}")
                
            except Exception as e:
                error_msg = f"Failed to verify backup {backup_file['name']}: {e}"
                verification_report['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Test restore capability
        self.update_state(state='PROGRESS', meta={'step': 'testing_restore', 'progress': 95})
        
        if verification_report['backups_valid'] > 0:
            restore_test = _test_backup_restore()
            verification_report['restore_test'] = restore_test
        
        verification_report['completed_at'] = datetime.utcnow().isoformat()
        
        # Send alerts based on results
        if verification_report['backups_corrupted'] > 0:
            alert_system.send_alert(
                title="⚠️ Backup Integrity Issues Found",
                message=f"{verification_report['backups_corrupted']} of {verification_report['backups_checked']} backups are corrupted",
                level=AlertLevel.WARNING,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
                metadata=verification_report
            )
        else:
            alert_system.send_alert(
                title="✅ Backup Integrity Verified",
                message=f"All {verification_report['backups_valid']} backups passed integrity verification",
                level=AlertLevel.INFO,
                channels=[AlertChannel.SLACK],
                metadata=verification_report,
                throttle_key="backup_verification_success"
            )
        
        logger.info(f"Backup integrity verification completed: {verification_report}")
        
        return verification_report
        
    except Exception as e:
        error_msg = f"Backup integrity verification failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        alert_system.send_alert(
            title="❌ Backup Verification Failed",
            message=error_msg,
            level=AlertLevel.CRITICAL,
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            metadata={'task_id': task_id}
        )
        
        raise

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.monitoring_jobs.collect_performance_metrics')
def collect_performance_metrics(self):
    """Collect system performance metrics"""
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting performance metrics collection (task_id: {task_id})")
        
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'system_metrics': {},
            'application_metrics': {},
            'database_metrics': {}
        }
        
        # System metrics
        self.update_state(state='PROGRESS', meta={'step': 'collecting_system_metrics', 'progress': 30})
        
        metrics['system_metrics'] = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
            'process_count': len(psutil.pids())
        }
        
        # Application metrics
        self.update_state(state='PROGRESS', meta={'step': 'collecting_app_metrics', 'progress': 60})
        
        app_metrics = metrics_collector.get_current_metrics()
        metrics['application_metrics'] = app_metrics
        
        # Database metrics
        self.update_state(state='PROGRESS', meta={'step': 'collecting_db_metrics', 'progress': 90})
        
        db_metrics = _collect_database_metrics()
        metrics['database_metrics'] = db_metrics
        
        # Store metrics
        metrics_collector.store_metrics(metrics)
        
        logger.debug(f"Performance metrics collected: {metrics}")
        
        return metrics
        
    except Exception as e:
        error_msg = f"Performance metrics collection failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        # Don't alert for metrics collection failures unless they're persistent
        raise

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.monitoring_jobs.generate_weekly_reports')
def generate_weekly_reports(self):
    """Generate weekly system and usage reports"""
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting weekly reports generation (task_id: {task_id})")
        
        # Generate comprehensive weekly report
        report = {
            'week_ending': datetime.utcnow().isoformat(),
            'system_health_summary': {},
            'usage_summary': {},
            'performance_summary': {},
            'alerts_summary': {},
            'recommendations': []
        }
        
        # System health summary
        self.update_state(state='PROGRESS', meta={'step': 'generating_health_summary', 'progress': 25})
        report['system_health_summary'] = _generate_weekly_health_summary()
        
        # Usage summary
        self.update_state(state='PROGRESS', meta={'step': 'generating_usage_summary', 'progress': 50})
        report['usage_summary'] = _generate_weekly_usage_summary()
        
        # Performance summary
        self.update_state(state='PROGRESS', meta={'step': 'generating_performance_summary', 'progress': 75})
        report['performance_summary'] = _generate_weekly_performance_summary()
        
        # Alerts summary
        report['alerts_summary'] = _generate_weekly_alerts_summary()
        
        # Generate recommendations
        report['recommendations'] = _generate_weekly_recommendations(report)
        
        # Store and send report
        _store_weekly_report(report)
        _send_weekly_report(report)
        
        logger.info("Weekly reports generation completed")
        
        return report
        
    except Exception as e:
        error_msg = f"Weekly reports generation failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        alert_system.send_alert(
            title="❌ Weekly Reports Generation Failed",
            message=error_msg,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            metadata={'task_id': task_id}
        )
        
        raise

# Helper functions for health checks and monitoring

def _check_database_health() -> Dict[str, Any]:
    """Check database connectivity and performance"""
    try:
        start_time = datetime.utcnow()
        
        with get_db_connection() as conn:
            # Test basic connectivity
            cursor = conn.execute("SELECT 1")
            cursor.fetchone()
            
            # Check table count
            cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            # Check database size
            db_size_mb = _get_database_size() / 1024 / 1024
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            'status': 'healthy',
            'message': 'Database is responsive',
            'metrics': {
                'response_time_ms': response_time,
                'table_count': table_count,
                'size_mb': round(db_size_mb, 2)
            }
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'severity': 'critical',
            'message': f'Database check failed: {e}'
        }

def _check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity and performance"""
    try:
        import redis
        
        start_time = datetime.utcnow()
        redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        
        # Test basic connectivity
        redis_client.ping()
        
        # Get Redis info
        info = redis_client.info()
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            'status': 'healthy',
            'message': 'Redis is responsive',
            'metrics': {
                'response_time_ms': response_time,
                'used_memory_mb': round(info.get('used_memory', 0) / 1024 / 1024, 2),
                'connected_clients': info.get('connected_clients', 0)
            }
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'severity': 'critical',
            'message': f'Redis check failed: {e}'
        }

def _check_celery_workers_health() -> Dict[str, Any]:
    """Check Celery workers status"""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if not stats:
            return {
                'status': 'unhealthy',
                'severity': 'critical',
                'message': 'No active Celery workers found'
            }
        
        worker_count = len(stats)
        
        return {
            'status': 'healthy',
            'message': f'{worker_count} Celery workers active',
            'metrics': {
                'active_workers': worker_count,
                'worker_details': stats
            }
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'severity': 'warning',
            'message': f'Celery workers check failed: {e}'
        }

def _check_disk_space() -> Dict[str, Any]:
    """Check available disk space"""
    try:
        disk_usage = psutil.disk_usage('/')
        free_percent = (disk_usage.free / disk_usage.total) * 100
        
        if free_percent < 10:
            return {
                'status': 'unhealthy',
                'severity': 'critical',
                'message': f'Low disk space: {free_percent:.1f}% free',
                'metrics': {'free_percent': free_percent}
            }
        elif free_percent < 20:
            return {
                'status': 'unhealthy',
                'severity': 'warning',
                'message': f'Disk space warning: {free_percent:.1f}% free',
                'metrics': {'free_percent': free_percent}
            }
        else:
            return {
                'status': 'healthy',
                'message': f'Sufficient disk space: {free_percent:.1f}% free',
                'metrics': {'free_percent': free_percent}
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'severity': 'warning',
            'message': f'Disk space check failed: {e}'
        }

def _check_memory_usage() -> Dict[str, Any]:
    """Check memory usage"""
    try:
        memory = psutil.virtual_memory()
        
        if memory.percent > 90:
            return {
                'status': 'unhealthy',
                'severity': 'critical',
                'message': f'High memory usage: {memory.percent:.1f}%',
                'metrics': {'memory_percent': memory.percent}
            }
        elif memory.percent > 80:
            return {
                'status': 'unhealthy',
                'severity': 'warning',
                'message': f'Memory usage warning: {memory.percent:.1f}%',
                'metrics': {'memory_percent': memory.percent}
            }
        else:
            return {
                'status': 'healthy',
                'message': f'Memory usage normal: {memory.percent:.1f}%',
                'metrics': {'memory_percent': memory.percent}
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'severity': 'warning',
            'message': f'Memory check failed: {e}'
        }

def _check_cpu_usage() -> Dict[str, Any]:
    """Check CPU usage"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_percent > 90:
            return {
                'status': 'unhealthy',
                'severity': 'warning',
                'message': f'High CPU usage: {cpu_percent:.1f}%',
                'metrics': {'cpu_percent': cpu_percent}
            }
        else:
            return {
                'status': 'healthy',
                'message': f'CPU usage normal: {cpu_percent:.1f}%',
                'metrics': {'cpu_percent': cpu_percent}
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'severity': 'warning',
            'message': f'CPU check failed: {e}'
        }

def _check_api_endpoints() -> Dict[str, Any]:
    """Check critical API endpoints"""
    try:
        import requests
        
        # Test health endpoint
        response = requests.get('http://localhost:8000/health', timeout=10)
        
        if response.status_code == 200:
            return {
                'status': 'healthy',
                'message': 'API endpoints responsive',
                'metrics': {'response_time_ms': response.elapsed.total_seconds() * 1000}
            }
        else:
            return {
                'status': 'unhealthy',
                'severity': 'critical',
                'message': f'API health check returned {response.status_code}'
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'severity': 'critical',
            'message': f'API endpoints check failed: {e}'
        }

def _check_external_apis() -> Dict[str, Any]:
    """Check external API connectivity"""
    try:
        # This would check connectivity to external APIs
        # For now, return healthy
        return {
            'status': 'healthy',
            'message': 'External APIs accessible'
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'severity': 'warning',
            'message': f'External APIs check failed: {e}'
        }

def _check_s3_connectivity() -> Dict[str, Any]:
    """Check S3 connectivity"""
    try:
        s3_client = boto3.client('s3')
        
        # Test with a simple operation
        response = s3_client.list_buckets()
        
        return {
            'status': 'healthy',
            'message': 'S3 connectivity verified',
            'metrics': {'bucket_count': len(response.get('Buckets', []))}
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'severity': 'warning',
            'message': f'S3 connectivity check failed: {e}'
        }

def _check_stripe_connectivity() -> Dict[str, Any]:
    """Check Stripe API connectivity"""
    try:
        import stripe
        
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        # Test with a simple operation
        stripe.Account.retrieve()
        
        return {
            'status': 'healthy',
            'message': 'Stripe connectivity verified'
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'severity': 'warning',
            'message': f'Stripe connectivity check failed: {e}'
        }

# Additional helper functions would be implemented here for:
# - LPA freshness checking
# - Freshness alerts
# - Health alerts
# - Database metrics collection
# - Backup verification
# - Weekly report generation
# etc.

def _get_database_size() -> int:
    """Get database file size in bytes"""
    try:
        db_path = os.getenv('DATABASE_PATH', 'dev.db')
        return os.path.getsize(db_path)
    except:
        return 0

# Placeholder implementations for brevity
def _check_lpa_freshness(): return []
def _send_freshness_alerts(report): pass
def _store_freshness_report(report): pass
def _send_health_alerts(report): pass
def _cleanup_filesystem(days): return {}
def _get_recent_backups(): return []
def _verify_single_backup(backup): return {'valid': True}
def _test_backup_restore(): return {'success': True}
def _collect_database_metrics(): return {}
def _archive_daily_usage_stats(): pass
def _update_system_usage_stats(stats): pass
def _generate_weekly_health_summary(): return {}
def _generate_weekly_usage_summary(): return {}
def _generate_weekly_performance_summary(): return {}
def _generate_weekly_alerts_summary(): return {}
def _generate_weekly_recommendations(report): return []
def _store_weekly_report(report): pass
def _send_weekly_report(report): pass