"""
Automated Backup System
Comprehensive backup solution for database, files, and configuration data
"""

import os
import asyncio
import shutil
import gzip
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import subprocess
import boto3
from botocore.exceptions import ClientError
import schedule
import time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import redis

logger = logging.getLogger(__name__)

class BackupConfig:
    """Configuration for backup system"""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.backup_root = os.getenv("BACKUP_ROOT", "/var/backups/domus")
        self.aws_s3_bucket = os.getenv("BACKUP_S3_BUCKET")
        self.aws_region = os.getenv("AWS_REGION", "us-west-2")
        
        # Retention policies
        self.daily_retention_days = int(os.getenv("DAILY_BACKUP_RETENTION", "30"))
        self.weekly_retention_weeks = int(os.getenv("WEEKLY_BACKUP_RETENTION", "12"))
        self.monthly_retention_months = int(os.getenv("MONTHLY_BACKUP_RETENTION", "12"))
        
        # File paths
        self.document_storage_path = os.getenv("DOCUMENT_STORAGE_PATH", "/app/documents")
        self.config_backup_paths = [
            "/app/config",
            "/app/.env",
            "/app/docker-compose.yml",
            "/app/requirements.txt"
        ]

class DatabaseBackup:
    """Handle database backup operations"""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.engine = create_engine(config.database_url)
        
    def create_dump(self, output_path: str) -> bool:
        """Create PostgreSQL database dump"""
        try:
            # Extract database connection details
            from urllib.parse import urlparse
            parsed = urlparse(self.config.database_url)
            
            env = os.environ.copy()
            env['PGPASSWORD'] = parsed.password
            
            cmd = [
                'pg_dump',
                '--host', parsed.hostname,
                '--port', str(parsed.port or 5432),
                '--username', parsed.username,
                '--dbname', parsed.path[1:],  # Remove leading slash
                '--format=custom',
                '--compress=9',
                '--file', output_path
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database backup created successfully: {output_path}")
                return True
            else:
                logger.error(f"Database backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Database backup error: {e}")
            return False
    
    def restore_dump(self, dump_path: str, target_db: Optional[str] = None) -> bool:
        """Restore database from dump file"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.config.database_url)
            
            env = os.environ.copy()
            env['PGPASSWORD'] = parsed.password
            
            database = target_db or parsed.path[1:]
            
            cmd = [
                'pg_restore',
                '--host', parsed.hostname,
                '--port', str(parsed.port or 5432),
                '--username', parsed.username,
                '--dbname', database,
                '--clean',
                '--if-exists',
                '--no-owner',
                '--no-privileges',
                dump_path
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database restored successfully from: {dump_path}")
                return True
            else:
                logger.error(f"Database restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Database restore error: {e}")
            return False
    
    def get_database_size(self) -> int:
        """Get current database size in bytes"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT pg_database_size(current_database()) as size
                """))
                return result.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting database size: {e}")
            return 0
    
    def get_table_sizes(self) -> Dict[str, int]:
        """Get sizes of all tables"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        tablename,
                        pg_total_relation_size(schemaname||'.'||tablename) as size
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY size DESC
                """))
                return dict(result.fetchall())
        except Exception as e:
            logger.error(f"Error getting table sizes: {e}")
            return {}

class RedisBackup:
    """Handle Redis backup operations"""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.redis_client = redis.from_url(config.redis_url)
    
    def create_dump(self, output_path: str) -> bool:
        """Create Redis backup"""
        try:
            # Get all Redis data
            data = {}
            
            # Get all keys
            keys = self.redis_client.keys('*')
            
            for key in keys:
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                key_type = self.redis_client.type(key)
                
                if key_type == b'string':
                    data[key_str] = {
                        'type': 'string',
                        'value': self.redis_client.get(key).decode('utf-8')
                    }
                elif key_type == b'hash':
                    data[key_str] = {
                        'type': 'hash',
                        'value': {k.decode('utf-8'): v.decode('utf-8') 
                                for k, v in self.redis_client.hgetall(key).items()}
                    }
                elif key_type == b'list':
                    data[key_str] = {
                        'type': 'list',
                        'value': [item.decode('utf-8') for item in self.redis_client.lrange(key, 0, -1)]
                    }
                elif key_type == b'set':
                    data[key_str] = {
                        'type': 'set',
                        'value': [item.decode('utf-8') for item in self.redis_client.smembers(key)]
                    }
                elif key_type == b'zset':
                    data[key_str] = {
                        'type': 'zset',
                        'value': [(member.decode('utf-8'), score) 
                                for member, score in self.redis_client.zrange(key, 0, -1, withscores=True)]
                    }
                
                # Get TTL if exists
                ttl = self.redis_client.ttl(key)
                if ttl > 0:
                    data[key_str]['ttl'] = ttl
            
            # Save to compressed JSON file
            with gzip.open(output_path, 'wt', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Redis backup created successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Redis backup error: {e}")
            return False
    
    def restore_dump(self, dump_path: str) -> bool:
        """Restore Redis from dump file"""
        try:
            # Clear existing data (with confirmation)
            logger.warning("Restoring Redis will clear all existing data")
            
            with gzip.open(dump_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            # Clear database
            self.redis_client.flushdb()
            
            # Restore data
            for key, item in data.items():
                item_type = item['type']
                value = item['value']
                ttl = item.get('ttl')
                
                if item_type == 'string':
                    self.redis_client.set(key, value)
                elif item_type == 'hash':
                    self.redis_client.hset(key, mapping=value)
                elif item_type == 'list':
                    for list_item in value:
                        self.redis_client.lpush(key, list_item)
                elif item_type == 'set':
                    for set_item in value:
                        self.redis_client.sadd(key, set_item)
                elif item_type == 'zset':
                    for member, score in value:
                        self.redis_client.zadd(key, {member: score})
                
                # Set TTL if it existed
                if ttl:
                    self.redis_client.expire(key, ttl)
            
            logger.info(f"Redis restored successfully from: {dump_path}")
            return True
            
        except Exception as e:
            logger.error(f"Redis restore error: {e}")
            return False

class FileBackup:
    """Handle file system backup operations"""
    
    def __init__(self, config: BackupConfig):
        self.config = config
    
    def create_archive(self, source_path: str, output_path: str, exclude_patterns: List[str] = None) -> bool:
        """Create compressed archive of directory"""
        try:
            exclude_patterns = exclude_patterns or []
            
            # Create directory structure
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Build tar command with exclusions
            cmd = ['tar', '-czf', output_path, '-C', os.path.dirname(source_path)]
            
            for pattern in exclude_patterns:
                cmd.extend(['--exclude', pattern])
            
            cmd.append(os.path.basename(source_path))
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"File archive created successfully: {output_path}")
                return True
            else:
                logger.error(f"File archive failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"File backup error: {e}")
            return False
    
    def restore_archive(self, archive_path: str, target_path: str) -> bool:
        """Restore files from archive"""
        try:
            # Create target directory
            os.makedirs(target_path, exist_ok=True)
            
            cmd = ['tar', '-xzf', archive_path, '-C', target_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Files restored successfully to: {target_path}")
                return True
            else:
                logger.error(f"File restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"File restore error: {e}")
            return False
    
    def get_directory_size(self, path: str) -> int:
        """Get total size of directory in bytes"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            return total_size
        except Exception as e:
            logger.error(f"Error calculating directory size: {e}")
            return 0

class S3Storage:
    """Handle S3 backup storage operations"""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.s3_client = boto3.client('s3', region_name=config.aws_region)
        self.bucket = config.aws_s3_bucket
    
    def upload_file(self, local_path: str, s3_key: str) -> bool:
        """Upload file to S3"""
        try:
            self.s3_client.upload_file(local_path, self.bucket, s3_key)
            logger.info(f"File uploaded to S3: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return False
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """Download file from S3"""
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3_client.download_file(self.bucket, s3_key, local_path)
            logger.info(f"File downloaded from S3: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            return False
    
    def list_backups(self, prefix: str = "") -> List[Dict]:
        """List backup files in S3"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })
            
            return files
        except ClientError as e:
            logger.error(f"S3 list failed: {e}")
            return []
    
    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info(f"File deleted from S3: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            return False

class BackupManager:
    """Main backup management class"""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.db_backup = DatabaseBackup(config)
        self.redis_backup = RedisBackup(config)
        self.file_backup = FileBackup(config)
        self.s3_storage = S3Storage(config) if config.aws_s3_bucket else None
        
        # Ensure backup directories exist
        os.makedirs(config.backup_root, exist_ok=True)
    
    def create_full_backup(self, backup_type: str = "daily") -> Dict[str, Any]:
        """Create complete system backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{backup_type}_{timestamp}"
        
        backup_dir = os.path.join(self.config.backup_root, backup_id)
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_manifest = {
            "backup_id": backup_id,
            "backup_type": backup_type,
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat(),
            "components": {},
            "success": True,
            "errors": []
        }
        
        # Database backup
        try:
            db_file = os.path.join(backup_dir, "database.dump")
            if self.db_backup.create_dump(db_file):
                backup_manifest["components"]["database"] = {
                    "file": "database.dump",
                    "size": os.path.getsize(db_file),
                    "success": True
                }
            else:
                backup_manifest["errors"].append("Database backup failed")
                backup_manifest["success"] = False
        except Exception as e:
            backup_manifest["errors"].append(f"Database backup error: {e}")
            backup_manifest["success"] = False
        
        # Redis backup
        try:
            redis_file = os.path.join(backup_dir, "redis.json.gz")
            if self.redis_backup.create_dump(redis_file):
                backup_manifest["components"]["redis"] = {
                    "file": "redis.json.gz",
                    "size": os.path.getsize(redis_file),
                    "success": True
                }
            else:
                backup_manifest["errors"].append("Redis backup failed")
        except Exception as e:
            backup_manifest["errors"].append(f"Redis backup error: {e}")
        
        # Document files backup
        try:
            if os.path.exists(self.config.document_storage_path):
                docs_file = os.path.join(backup_dir, "documents.tar.gz")
                if self.file_backup.create_archive(
                    self.config.document_storage_path, 
                    docs_file,
                    exclude_patterns=['*.tmp', '*.log', '__pycache__']
                ):
                    backup_manifest["components"]["documents"] = {
                        "file": "documents.tar.gz",
                        "size": os.path.getsize(docs_file),
                        "success": True
                    }
                else:
                    backup_manifest["errors"].append("Document files backup failed")
        except Exception as e:
            backup_manifest["errors"].append(f"Document backup error: {e}")
        
        # Configuration backup
        try:
            config_file = os.path.join(backup_dir, "config.tar.gz")
            # Create temporary directory with config files
            temp_config_dir = os.path.join(backup_dir, "temp_config")
            os.makedirs(temp_config_dir, exist_ok=True)
            
            for config_path in self.config.config_backup_paths:
                if os.path.exists(config_path):
                    if os.path.isfile(config_path):
                        shutil.copy2(config_path, temp_config_dir)
                    else:
                        shutil.copytree(
                            config_path, 
                            os.path.join(temp_config_dir, os.path.basename(config_path)),
                            dirs_exist_ok=True
                        )
            
            if self.file_backup.create_archive(temp_config_dir, config_file):
                backup_manifest["components"]["config"] = {
                    "file": "config.tar.gz",
                    "size": os.path.getsize(config_file),
                    "success": True
                }
            
            # Clean up temp directory
            shutil.rmtree(temp_config_dir)
            
        except Exception as e:
            backup_manifest["errors"].append(f"Config backup error: {e}")
        
        # Save backup manifest
        manifest_file = os.path.join(backup_dir, "backup_manifest.json")
        with open(manifest_file, 'w') as f:
            json.dump(backup_manifest, f, indent=2)
        
        # Upload to S3 if configured
        if self.s3_storage:
            try:
                s3_prefix = f"backups/{backup_id}/"
                
                for file in os.listdir(backup_dir):
                    local_file = os.path.join(backup_dir, file)
                    s3_key = f"{s3_prefix}{file}"
                    
                    if self.s3_storage.upload_file(local_file, s3_key):
                        logger.info(f"Uploaded to S3: {s3_key}")
                    else:
                        backup_manifest["errors"].append(f"S3 upload failed: {file}")
                        
            except Exception as e:
                backup_manifest["errors"].append(f"S3 upload error: {e}")
        
        # Update final manifest
        with open(manifest_file, 'w') as f:
            json.dump(backup_manifest, f, indent=2)
        
        logger.info(f"Backup completed: {backup_id}")
        return backup_manifest
    
    def restore_backup(self, backup_id: str, components: List[str] = None) -> Dict[str, Any]:
        """Restore from backup"""
        backup_dir = os.path.join(self.config.backup_root, backup_id)
        manifest_file = os.path.join(backup_dir, "backup_manifest.json")
        
        if not os.path.exists(manifest_file):
            # Try to download from S3
            if self.s3_storage:
                s3_key = f"backups/{backup_id}/backup_manifest.json"
                if not self.s3_storage.download_file(s3_key, manifest_file):
                    return {"success": False, "error": "Backup not found"}
            else:
                return {"success": False, "error": "Backup not found"}
        
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        components = components or list(manifest["components"].keys())
        restore_result = {
            "backup_id": backup_id,
            "restored_components": [],
            "errors": [],
            "success": True
        }
        
        for component in components:
            if component not in manifest["components"]:
                restore_result["errors"].append(f"Component not found: {component}")
                continue
            
            component_file = manifest["components"][component]["file"]
            local_file = os.path.join(backup_dir, component_file)
            
            # Download from S3 if not local
            if not os.path.exists(local_file) and self.s3_storage:
                s3_key = f"backups/{backup_id}/{component_file}"
                if not self.s3_storage.download_file(s3_key, local_file):
                    restore_result["errors"].append(f"Failed to download: {component}")
                    continue
            
            # Restore component
            try:
                if component == "database":
                    if self.db_backup.restore_dump(local_file):
                        restore_result["restored_components"].append(component)
                    else:
                        restore_result["errors"].append(f"Database restore failed")
                        
                elif component == "redis":
                    if self.redis_backup.restore_dump(local_file):
                        restore_result["restored_components"].append(component)
                    else:
                        restore_result["errors"].append(f"Redis restore failed")
                        
                elif component == "documents":
                    if self.file_backup.restore_archive(local_file, self.config.document_storage_path):
                        restore_result["restored_components"].append(component)
                    else:
                        restore_result["errors"].append(f"Documents restore failed")
                        
                elif component == "config":
                    temp_restore_dir = "/tmp/config_restore"
                    if self.file_backup.restore_archive(local_file, temp_restore_dir):
                        # Manual config restoration requires admin intervention
                        restore_result["restored_components"].append(component)
                        restore_result["config_location"] = temp_restore_dir
                    else:
                        restore_result["errors"].append(f"Config restore failed")
                        
            except Exception as e:
                restore_result["errors"].append(f"{component} restore error: {e}")
        
        if restore_result["errors"]:
            restore_result["success"] = False
        
        return restore_result
    
    def cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        try:
            backups = []
            
            # Get local backups
            if os.path.exists(self.config.backup_root):
                for backup_dir in os.listdir(self.config.backup_root):
                    manifest_path = os.path.join(self.config.backup_root, backup_dir, "backup_manifest.json")
                    if os.path.exists(manifest_path):
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                            backups.append({
                                "id": backup_dir,
                                "type": manifest.get("backup_type", "unknown"),
                                "created_at": datetime.fromisoformat(manifest["created_at"]),
                                "local": True
                            })
            
            # Get S3 backups
            if self.s3_storage:
                s3_backups = self.s3_storage.list_backups("backups/")
                # Parse S3 backup info
                # Implementation would parse S3 structure
            
            now = datetime.now()
            to_delete = []
            
            for backup in backups:
                age = now - backup["created_at"]
                backup_type = backup["type"]
                
                should_delete = False
                
                if backup_type == "daily" and age.days > self.config.daily_retention_days:
                    should_delete = True
                elif backup_type == "weekly" and age.days > (self.config.weekly_retention_weeks * 7):
                    should_delete = True
                elif backup_type == "monthly" and age.days > (self.config.monthly_retention_months * 30):
                    should_delete = True
                
                if should_delete:
                    to_delete.append(backup)
            
            # Delete old backups
            for backup in to_delete:
                backup_path = os.path.join(self.config.backup_root, backup["id"])
                if os.path.exists(backup_path):
                    shutil.rmtree(backup_path)
                    logger.info(f"Deleted old backup: {backup['id']}")
                
                # Delete from S3
                if self.s3_storage:
                    s3_files = self.s3_storage.list_backups(f"backups/{backup['id']}/")
                    for s3_file in s3_files:
                        self.s3_storage.delete_file(s3_file["key"])
            
            logger.info(f"Cleaned up {len(to_delete)} old backups")
            
        except Exception as e:
            logger.error(f"Backup cleanup error: {e}")
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get comprehensive backup system status"""
        status = {
            "last_backup": None,
            "backup_count": 0,
            "total_backup_size": 0,
            "storage_locations": [],
            "retention_policy": {
                "daily": f"{self.config.daily_retention_days} days",
                "weekly": f"{self.config.weekly_retention_weeks} weeks", 
                "monthly": f"{self.config.monthly_retention_months} months"
            },
            "health_checks": {}
        }
        
        # Check local backups
        if os.path.exists(self.config.backup_root):
            backups = []
            total_size = 0
            
            for backup_dir in os.listdir(self.config.backup_root):
                backup_path = os.path.join(self.config.backup_root, backup_dir)
                if os.path.isdir(backup_path):
                    manifest_path = os.path.join(backup_path, "backup_manifest.json")
                    if os.path.exists(manifest_path):
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                            backups.append(manifest)
                            
                        # Calculate directory size
                        for root, dirs, files in os.walk(backup_path):
                            for file in files:
                                total_size += os.path.getsize(os.path.join(root, file))
            
            status["backup_count"] = len(backups)
            status["total_backup_size"] = total_size
            status["storage_locations"].append("local")
            
            if backups:
                latest_backup = max(backups, key=lambda x: x["created_at"])
                status["last_backup"] = latest_backup
        
        # Check S3 availability
        if self.s3_storage:
            try:
                self.s3_storage.s3_client.head_bucket(Bucket=self.s3_storage.bucket)
                status["storage_locations"].append("s3")
                status["health_checks"]["s3"] = "healthy"
            except Exception as e:
                status["health_checks"]["s3"] = f"error: {e}"
        
        # Check database connectivity
        try:
            size = self.db_backup.get_database_size()
            status["health_checks"]["database"] = "healthy"
            status["database_size"] = size
        except Exception as e:
            status["health_checks"]["database"] = f"error: {e}"
        
        # Check Redis connectivity
        try:
            self.redis_backup.redis_client.ping()
            status["health_checks"]["redis"] = "healthy"
        except Exception as e:
            status["health_checks"]["redis"] = f"error: {e}"
        
        return status