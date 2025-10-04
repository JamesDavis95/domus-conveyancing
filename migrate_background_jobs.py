"""
Database Migration for Background Jobs and Monitoring System
Creates tables for job tracking, freshness monitoring, and system metrics
"""

import sqlite3
import os
from datetime import datetime

def migrate_background_jobs_schema():
    """Create tables for background jobs and monitoring system"""
    
    db_path = os.getenv('DATABASE_PATH', 'dev.db')
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        print("Creating background jobs and monitoring schema...")
        
        # Knowledge freshness tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_freshness (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL UNIQUE,
                last_updated TIMESTAMP NOT NULL,
                status TEXT NOT NULL DEFAULT 'fresh',
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # LPA-specific freshness tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lpa_freshness (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lpa_code TEXT NOT NULL UNIQUE,
                last_updated TIMESTAMP NOT NULL,
                status TEXT NOT NULL DEFAULT 'fresh',
                data_sources TEXT, -- JSON of data sources updated
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Job execution logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                job_name TEXT NOT NULL,
                status TEXT NOT NULL, -- pending, running, success, failure, retry
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                duration_seconds REAL,
                result_data TEXT, -- JSON
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                worker_name TEXT,
                queue_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # System health metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT NOT NULL, -- cpu, memory, disk, api_response_time, etc.
                metric_value REAL NOT NULL,
                metric_unit TEXT, -- percent, mb, ms, etc.
                component TEXT, -- system, database, api, etc.
                details TEXT, -- JSON for additional details
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Usage analytics (extended from existing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                feature TEXT NOT NULL,
                usage_count INTEGER NOT NULL DEFAULT 1,
                usage_type TEXT, -- api_call, search, generation, etc.
                metadata TEXT, -- JSON
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (org_id) REFERENCES organizations (id)
            )
        """)
        
        # Alert history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                level TEXT NOT NULL, -- info, warning, error, critical
                channels TEXT NOT NULL, -- JSON array
                delivery_status TEXT, -- JSON object
                sent_at TIMESTAMP,
                retry_count INTEGER DEFAULT 0,
                metadata TEXT, -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # API request logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER,
                response_time_ms REAL,
                user_id INTEGER,
                org_id INTEGER,
                ip_address TEXT,
                user_agent TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (org_id) REFERENCES organizations (id)
            )
        """)
        
        # Search query logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                org_id INTEGER,
                query_text TEXT NOT NULL,
                query_type TEXT, -- semantic, keyword, hybrid
                results_count INTEGER,
                response_time_ms REAL,
                filters_applied TEXT, -- JSON
                clicked_results TEXT, -- JSON array of clicked result IDs
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (org_id) REFERENCES organizations (id)
            )
        """)
        
        # LPA HDT (Housing Delivery Test) data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lpa_hdt_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lpa_code TEXT NOT NULL,
                measurement_year INTEGER NOT NULL,
                delivery_percentage REAL,
                homes_required INTEGER,
                homes_delivered INTEGER,
                action_plan_required BOOLEAN DEFAULT FALSE,
                presumption_applies BOOLEAN DEFAULT FALSE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(lpa_code, measurement_year)
            )
        """)
        
        # LPA 5YHLS (5-Year Housing Land Supply) data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lpa_5yhls_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lpa_code TEXT NOT NULL,
                assessment_date DATE,
                supply_years REAL, -- e.g., 4.2 years
                deliverable_homes INTEGER,
                annual_requirement INTEGER,
                supply_buffer TEXT, -- 5%, 10%, 20%
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(lpa_code, assessment_date)
            )
        """)
        
        # Background job schedules (for dynamic scheduling)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT NOT NULL UNIQUE,
                schedule_expression TEXT NOT NULL, -- cron expression
                enabled BOOLEAN DEFAULT TRUE,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                run_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                timeout_seconds INTEGER DEFAULT 3600,
                queue_name TEXT DEFAULT 'default',
                metadata TEXT, -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Performance budgets and SLA tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL UNIQUE,
                target_value REAL NOT NULL,
                warning_threshold REAL,
                critical_threshold REAL,
                unit TEXT NOT NULL, -- ms, percent, count, etc.
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Performance SLA violations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sla_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                measured_value REAL NOT NULL,
                target_value REAL NOT NULL,
                violation_type TEXT NOT NULL, -- warning, critical
                duration_seconds INTEGER,
                resolved_at TIMESTAMP,
                metadata TEXT, -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (metric_name) REFERENCES performance_budgets (metric_name)
            )
        """)
        
        # Weekly reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_ending DATE NOT NULL UNIQUE,
                report_data TEXT NOT NULL, -- JSON
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Temp files tracking (for cleanup)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temp_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                purpose TEXT, -- upload, processing, export, etc.
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("Creating indexes for performance...")
        
        # Create indexes for better query performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_knowledge_freshness_type ON knowledge_freshness(type)",
            "CREATE INDEX IF NOT EXISTS idx_lpa_freshness_code ON lpa_freshness(lpa_code)",
            "CREATE INDEX IF NOT EXISTS idx_job_logs_name_status ON job_execution_logs(job_name, status)",
            "CREATE INDEX IF NOT EXISTS idx_job_logs_created ON job_execution_logs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_type_recorded ON system_metrics(metric_type, recorded_at)",
            "CREATE INDEX IF NOT EXISTS idx_usage_analytics_org_feature ON usage_analytics(org_id, feature)",
            "CREATE INDEX IF NOT EXISTS idx_usage_analytics_recorded ON usage_analytics(recorded_at)",
            "CREATE INDEX IF NOT EXISTS idx_alert_history_level_created ON alert_history(level, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint_created ON api_logs(endpoint, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_api_logs_org_created ON api_logs(org_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_search_queries_org_created ON search_queries(org_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_hdt_data_lpa_year ON lpa_hdt_data(lpa_code, measurement_year)",
            "CREATE INDEX IF NOT EXISTS idx_5yhls_data_lpa_date ON lpa_5yhls_data(lpa_code, assessment_date)",
            "CREATE INDEX IF NOT EXISTS idx_job_schedules_enabled_next_run ON job_schedules(enabled, next_run)",
            "CREATE INDEX IF NOT EXISTS idx_sla_violations_metric_created ON sla_violations(metric_name, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_temp_files_expires ON temp_files(expires_at)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        print("Inserting default data...")
        
        # Insert default performance budgets
        performance_budgets = [
            ('api_response_time_p95', 300.0, 250.0, 500.0, 'ms'),
            ('planning_ai_response_time', 10000.0, 8000.0, 15000.0, 'ms'),
            ('ttfb', 1500.0, 1200.0, 2000.0, 'ms'),
            ('cpu_usage', 80.0, 70.0, 90.0, 'percent'),
            ('memory_usage', 80.0, 70.0, 90.0, 'percent'),
            ('disk_usage', 80.0, 70.0, 90.0, 'percent'),
            ('database_response_time', 100.0, 80.0, 200.0, 'ms'),
            ('error_rate', 1.0, 0.5, 2.0, 'percent')
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO performance_budgets 
            (metric_name, target_value, warning_threshold, critical_threshold, unit)
            VALUES (?, ?, ?, ?, ?)
        """, performance_budgets)
        
        # Insert default job schedules (these will be managed by Celery beat, but tracked here)
        job_schedules = [
            ('refresh_knowledge_base', '0 */6 * * *', True, 3600, 'rag_queue'),
            ('update_all_lpa_data', '0 3 * * *', True, 7200, 'lpa_queue'),
            ('ingest_appeals_objections', '30 */4 * * *', True, 3600, 'lpa_queue'),
            ('reset_daily_usage', '0 0 * * *', True, 300, 'monitoring_queue'),
            ('track_data_freshness', '0 */2 * * *', True, 600, 'monitoring_queue'),
            ('monitor_system_health', '*/15 * * * *', True, 300, 'monitoring_queue'),
            ('cleanup_old_data', '0 2 * * *', True, 1800, 'monitoring_queue'),
            ('verify_backup_integrity', '0 4 * * *', True, 1200, 'monitoring_queue'),
            ('collect_performance_metrics', '*/5 * * * *', True, 60, 'monitoring_queue'),
            ('generate_weekly_reports', '0 8 * * 0', True, 3600, 'monitoring_queue')
        ]
        
        for job_name, schedule, enabled, timeout, queue in job_schedules:
            cursor.execute("""
                INSERT OR IGNORE INTO job_schedules 
                (job_name, schedule_expression, enabled, timeout_seconds, queue_name)
                VALUES (?, ?, ?, ?, ?)
            """, (job_name, schedule, enabled, timeout, queue))
        
        # Insert initial freshness tracking records
        initial_freshness = [
            ('knowledge_base', datetime.utcnow(), 'stale'),
            ('lpa_data', datetime.utcnow(), 'stale'),
            ('appeals_data', datetime.utcnow(), 'stale'),
            ('constraints_data', datetime.utcnow(), 'stale'),
            ('hdt_5yhls_data', datetime.utcnow(), 'stale'),
            ('embeddings', datetime.utcnow(), 'stale'),
            ('marketplace_data', datetime.utcnow(), 'fresh')
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO knowledge_freshness 
            (type, last_updated, status)
            VALUES (?, ?, ?)
        """, initial_freshness)
        
        conn.commit()
        
        print("Background jobs and monitoring schema migration completed successfully!")
        print("\nCreated tables:")
        print("- knowledge_freshness")
        print("- lpa_freshness")
        print("- job_execution_logs")
        print("- system_metrics")
        print("- usage_analytics")
        print("- alert_history")
        print("- api_logs")
        print("- search_queries")
        print("- lpa_hdt_data")
        print("- lpa_5yhls_data")
        print("- job_schedules")
        print("- performance_budgets")
        print("- sla_violations")
        print("- weekly_reports")
        print("- temp_files")
        print("\nInserted default performance budgets and job schedules.")

if __name__ == "__main__":
    try:
        migrate_background_jobs_schema()
    except Exception as e:
        print(f"Migration failed: {e}")
        exit(1)