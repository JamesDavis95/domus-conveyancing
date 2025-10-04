"""
Data Archival System
Long-term data retention and compliance archival
"""

import os
import asyncio
import json
import gzip
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import hashlib
import csv
from pathlib import Path

logger = logging.getLogger(__name__)

class ArchivalTier(Enum):
    """Data archival storage tiers"""
    HOT = "hot"           # Immediate access (0-30 days)
    WARM = "warm"         # Quick access (30-90 days)
    COLD = "cold"         # Delayed access (90 days - 1 year)
    GLACIER = "glacier"   # Long-term archive (1+ years)

class RetentionClass(Enum):
    """Legal retention classifications"""
    TRANSACTION_RECORDS = "transaction_records"     # 6 years (SRA requirement)
    CLIENT_CORRESPONDENCE = "client_correspondence" # 6 years
    FINANCIAL_RECORDS = "financial_records"         # 7 years (tax requirement)
    REGULATORY_COMPLIANCE = "regulatory_compliance" # 10 years
    LEGAL_OPINIONS = "legal_opinions"              # 15 years
    PROPERTY_TITLES = "property_titles"            # Permanent

class DataClassification(Enum):
    """Data sensitivity classifications"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class ArchivalRecord:
    """Represents an archived data record"""
    
    def __init__(self, data_id: str, data_type: str, retention_class: RetentionClass, 
                 classification: DataClassification, original_size: int):
        self.record_id = f"arch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{data_id}"
        self.data_id = data_id
        self.data_type = data_type
        self.retention_class = retention_class
        self.classification = classification
        self.created_at = datetime.now()
        self.archived_at = None
        self.original_size = original_size
        self.compressed_size = None
        self.tier = ArchivalTier.HOT
        self.storage_location = None
        self.checksum = None
        self.metadata = {}
        self.retention_until = self._calculate_retention_date()
        self.access_log = []
    
    def _calculate_retention_date(self) -> datetime:
        """Calculate retention end date based on class"""
        retention_periods = {
            RetentionClass.TRANSACTION_RECORDS: timedelta(days=365 * 6),
            RetentionClass.CLIENT_CORRESPONDENCE: timedelta(days=365 * 6),
            RetentionClass.FINANCIAL_RECORDS: timedelta(days=365 * 7),
            RetentionClass.REGULATORY_COMPLIANCE: timedelta(days=365 * 10),
            RetentionClass.LEGAL_OPINIONS: timedelta(days=365 * 15),
            RetentionClass.PROPERTY_TITLES: timedelta(days=365 * 100)  # Effectively permanent
        }
        
        period = retention_periods.get(self.retention_class, timedelta(days=365 * 6))
        return self.created_at + period
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary"""
        return {
            "record_id": self.record_id,
            "data_id": self.data_id,
            "data_type": self.data_type,
            "retention_class": self.retention_class.value,
            "classification": self.classification.value,
            "created_at": self.created_at.isoformat(),
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "original_size": self.original_size,
            "compressed_size": self.compressed_size,
            "tier": self.tier.value,
            "storage_location": self.storage_location,
            "checksum": self.checksum,
            "metadata": self.metadata,
            "retention_until": self.retention_until.isoformat(),
            "access_count": len(self.access_log)
        }

class ArchivalStorage:
    """Handle different archival storage tiers"""
    
    def __init__(self, base_path: str = "/var/archive"):
        self.base_path = Path(base_path)
        self.tier_paths = {
            ArchivalTier.HOT: self.base_path / "hot",
            ArchivalTier.WARM: self.base_path / "warm", 
            ArchivalTier.COLD: self.base_path / "cold",
            ArchivalTier.GLACIER: self.base_path / "glacier"
        }
        
        # Create directory structure
        for tier_path in self.tier_paths.values():
            tier_path.mkdir(parents=True, exist_ok=True)
    
    def store_data(self, record: ArchivalRecord, data: bytes) -> bool:
        """Store data in appropriate tier"""
        try:
            tier_path = self.tier_paths[record.tier]
            file_path = tier_path / f"{record.record_id}.gz"
            
            # Compress and store data
            with gzip.open(file_path, 'wb') as f:
                f.write(data)
            
            # Calculate sizes and checksum
            record.compressed_size = file_path.stat().st_size
            record.checksum = self._calculate_checksum(data)
            record.storage_location = str(file_path)
            record.archived_at = datetime.now()
            
            logger.info(f"Archived data to {record.tier.value}: {record.record_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store archival data: {e}")
            return False
    
    def retrieve_data(self, record: ArchivalRecord) -> Optional[bytes]:
        """Retrieve data from archival storage"""
        try:
            if not record.storage_location or not os.path.exists(record.storage_location):
                logger.error(f"Archival data not found: {record.record_id}")
                return None
            
            with gzip.open(record.storage_location, 'rb') as f:
                data = f.read()
            
            # Verify checksum
            if record.checksum:
                current_checksum = self._calculate_checksum(data)
                if current_checksum != record.checksum:
                    logger.error(f"Checksum mismatch for {record.record_id}")
                    return None
            
            # Log access
            record.access_log.append({
                "accessed_at": datetime.now().isoformat(),
                "access_type": "retrieve"
            })
            
            logger.info(f"Retrieved archival data: {record.record_id}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to retrieve archival data: {e}")
            return None
    
    def move_to_tier(self, record: ArchivalRecord, new_tier: ArchivalTier) -> bool:
        """Move data between storage tiers"""
        try:
            if not record.storage_location or not os.path.exists(record.storage_location):
                return False
            
            old_path = Path(record.storage_location)
            new_tier_path = self.tier_paths[new_tier]
            new_path = new_tier_path / f"{record.record_id}.gz"
            
            # Move file
            old_path.rename(new_path)
            
            # Update record
            record.tier = new_tier
            record.storage_location = str(new_path)
            
            logger.info(f"Moved {record.record_id} to {new_tier.value} tier")
            return True
            
        except Exception as e:
            logger.error(f"Failed to move to tier: {e}")
            return False
    
    def delete_data(self, record: ArchivalRecord) -> bool:
        """Permanently delete archived data"""
        try:
            if record.storage_location and os.path.exists(record.storage_location):
                os.remove(record.storage_location)
                logger.info(f"Deleted archival data: {record.record_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete archival data: {e}")
            return False
    
    def _calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA-256 checksum of data"""
        return hashlib.sha256(data).hexdigest()

class ArchivalManager:
    """Main archival management system"""
    
    def __init__(self):
        self.storage = ArchivalStorage()
        self.records_db_path = Path("/var/archive/records.json")
        self.records: Dict[str, ArchivalRecord] = {}
        self.load_records()
        
        # Archival policies
        self.tier_migration_rules = {
            ArchivalTier.HOT: 30,      # Move to warm after 30 days
            ArchivalTier.WARM: 90,     # Move to cold after 90 days
            ArchivalTier.COLD: 365     # Move to glacier after 1 year
        }
    
    def load_records(self):
        """Load archival records from persistent storage"""
        try:
            if self.records_db_path.exists():
                with open(self.records_db_path, 'r') as f:
                    records_data = json.load(f)
                
                for record_id, record_dict in records_data.items():
                    record = ArchivalRecord(
                        record_dict["data_id"],
                        record_dict["data_type"],
                        RetentionClass(record_dict["retention_class"]),
                        DataClassification(record_dict["classification"]),
                        record_dict["original_size"]
                    )
                    
                    # Restore record state
                    record.record_id = record_dict["record_id"]
                    record.created_at = datetime.fromisoformat(record_dict["created_at"])
                    if record_dict["archived_at"]:
                        record.archived_at = datetime.fromisoformat(record_dict["archived_at"])
                    record.compressed_size = record_dict["compressed_size"]
                    record.tier = ArchivalTier(record_dict["tier"])
                    record.storage_location = record_dict["storage_location"]
                    record.checksum = record_dict["checksum"]
                    record.metadata = record_dict["metadata"]
                    record.retention_until = datetime.fromisoformat(record_dict["retention_until"])
                    record.access_log = record_dict.get("access_log", [])
                    
                    self.records[record_id] = record
                    
                logger.info(f"Loaded {len(self.records)} archival records")
                
        except Exception as e:
            logger.error(f"Failed to load archival records: {e}")
    
    def save_records(self):
        """Save archival records to persistent storage"""
        try:
            records_data = {}
            for record_id, record in self.records.items():
                records_data[record_id] = record.to_dict()
            
            # Create backup of existing records
            if self.records_db_path.exists():
                backup_path = self.records_db_path.with_suffix('.json.bak')
                self.records_db_path.rename(backup_path)
            
            with open(self.records_db_path, 'w') as f:
                json.dump(records_data, f, indent=2)
                
            logger.info("Saved archival records")
            
        except Exception as e:
            logger.error(f"Failed to save archival records: {e}")
    
    def archive_data(self, data_id: str, data: bytes, data_type: str, 
                    retention_class: RetentionClass, classification: DataClassification,
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[ArchivalRecord]:
        """Archive data with specified retention and classification"""
        
        try:
            # Create archival record
            record = ArchivalRecord(data_id, data_type, retention_class, classification, len(data))
            
            if metadata:
                record.metadata.update(metadata)
            
            # Store data
            if self.storage.store_data(record, data):
                self.records[record.record_id] = record
                self.save_records()
                
                logger.info(f"Archived data: {data_id} -> {record.record_id}")
                return record
            else:
                logger.error(f"Failed to archive data: {data_id}")
                return None
                
        except Exception as e:
            logger.error(f"Archive operation failed: {e}")
            return None
    
    def retrieve_archived_data(self, record_id: str) -> Optional[bytes]:
        """Retrieve archived data by record ID"""
        
        if record_id not in self.records:
            logger.error(f"Archival record not found: {record_id}")
            return None
        
        record = self.records[record_id]
        
        # Check if data is still within retention period
        if datetime.now() > record.retention_until:
            logger.warning(f"Data past retention period: {record_id}")
            # Depending on policy, might still allow access or deny
        
        data = self.storage.retrieve_data(record)
        
        if data:
            self.save_records()  # Save updated access log
        
        return data
    
    def search_records(self, criteria: Dict[str, Any]) -> List[ArchivalRecord]:
        """Search archival records by criteria"""
        
        results = []
        
        for record in self.records.values():
            match = True
            
            # Check each criterion
            for key, value in criteria.items():
                if key == "data_type" and record.data_type != value:
                    match = False
                    break
                elif key == "retention_class" and record.retention_class.value != value:
                    match = False
                    break
                elif key == "classification" and record.classification.value != value:
                    match = False
                    break
                elif key == "tier" and record.tier.value != value:
                    match = False
                    break
                elif key == "created_after" and record.created_at < datetime.fromisoformat(value):
                    match = False
                    break
                elif key == "created_before" and record.created_at > datetime.fromisoformat(value):
                    match = False
                    break
            
            if match:
                results.append(record)
        
        return results
    
    async def run_tier_migration(self):
        """Run automated tier migration based on age"""
        
        migrated_count = 0
        current_time = datetime.now()
        
        for record in self.records.values():
            if not record.archived_at:
                continue
            
            age_days = (current_time - record.archived_at).days
            current_tier = record.tier
            target_tier = None
            
            # Determine target tier based on age
            if current_tier == ArchivalTier.HOT and age_days >= self.tier_migration_rules[ArchivalTier.HOT]:
                target_tier = ArchivalTier.WARM
            elif current_tier == ArchivalTier.WARM and age_days >= self.tier_migration_rules[ArchivalTier.WARM]:
                target_tier = ArchivalTier.COLD
            elif current_tier == ArchivalTier.COLD and age_days >= self.tier_migration_rules[ArchivalTier.COLD]:
                target_tier = ArchivalTier.GLACIER
            
            # Migrate if needed
            if target_tier and self.storage.move_to_tier(record, target_tier):
                migrated_count += 1
                logger.info(f"Migrated {record.record_id} from {current_tier.value} to {target_tier.value}")
        
        if migrated_count > 0:
            self.save_records()
            logger.info(f"Tier migration completed: {migrated_count} records migrated")
    
    async def run_retention_cleanup(self) -> Dict[str, Any]:
        """Clean up data past retention period"""
        
        current_time = datetime.now()
        expired_records = []
        cleanup_results = {
            "expired_count": 0,
            "deleted_count": 0,
            "errors": [],
            "space_freed_bytes": 0
        }
        
        # Find expired records
        for record in self.records.values():
            if current_time > record.retention_until:
                expired_records.append(record)
        
        cleanup_results["expired_count"] = len(expired_records)
        
        # Delete expired records
        for record in expired_records:
            try:
                # Log before deletion for audit trail
                logger.info(f"Deleting expired record: {record.record_id} (expired: {record.retention_until})")
                
                if self.storage.delete_data(record):
                    cleanup_results["space_freed_bytes"] += record.compressed_size or 0
                    cleanup_results["deleted_count"] += 1
                    
                    # Remove from records
                    del self.records[record.record_id]
                else:
                    cleanup_results["errors"].append(f"Failed to delete {record.record_id}")
                    
            except Exception as e:
                cleanup_results["errors"].append(f"Error deleting {record.record_id}: {e}")
        
        if cleanup_results["deleted_count"] > 0:
            self.save_records()
        
        logger.info(f"Retention cleanup completed: {cleanup_results['deleted_count']} records deleted")
        return cleanup_results
    
    def generate_retention_report(self) -> Dict[str, Any]:
        """Generate comprehensive retention compliance report"""
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_records": len(self.records),
            "by_retention_class": {},
            "by_tier": {},
            "by_classification": {},
            "retention_status": {
                "active": 0,
                "near_expiry": 0,  # Within 30 days of expiry
                "expired": 0
            },
            "storage_summary": {
                "total_size_bytes": 0,
                "by_tier": {}
            }
        }
        
        current_time = datetime.now()
        near_expiry_threshold = timedelta(days=30)
        
        # Initialize counters
        for retention_class in RetentionClass:
            report["by_retention_class"][retention_class.value] = 0
        
        for tier in ArchivalTier:
            report["by_tier"][tier.value] = 0
            report["storage_summary"]["by_tier"][tier.value] = 0
        
        for classification in DataClassification:
            report["by_classification"][classification.value] = 0
        
        # Analyze records
        for record in self.records.values():
            # Count by retention class
            report["by_retention_class"][record.retention_class.value] += 1
            
            # Count by tier
            report["by_tier"][record.tier.value] += 1
            
            # Count by classification
            report["by_classification"][record.classification.value] += 1
            
            # Retention status
            if current_time > record.retention_until:
                report["retention_status"]["expired"] += 1
            elif (record.retention_until - current_time) <= near_expiry_threshold:
                report["retention_status"]["near_expiry"] += 1
            else:
                report["retention_status"]["active"] += 1
            
            # Storage size
            size = record.compressed_size or record.original_size
            report["storage_summary"]["total_size_bytes"] += size
            report["storage_summary"]["by_tier"][record.tier.value] += size
        
        return report
    
    def export_audit_trail(self, output_path: str) -> bool:
        """Export complete audit trail for compliance"""
        
        try:
            with open(output_path, 'w', newline='') as csvfile:
                fieldnames = [
                    'record_id', 'data_id', 'data_type', 'retention_class', 'classification',
                    'created_at', 'archived_at', 'retention_until', 'tier', 'original_size',
                    'compressed_size', 'checksum', 'access_count', 'last_accessed'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for record in self.records.values():
                    last_accessed = None
                    if record.access_log:
                        last_accessed = max(access["accessed_at"] for access in record.access_log)
                    
                    writer.writerow({
                        'record_id': record.record_id,
                        'data_id': record.data_id,
                        'data_type': record.data_type,
                        'retention_class': record.retention_class.value,
                        'classification': record.classification.value,
                        'created_at': record.created_at.isoformat(),
                        'archived_at': record.archived_at.isoformat() if record.archived_at else '',
                        'retention_until': record.retention_until.isoformat(),
                        'tier': record.tier.value,
                        'original_size': record.original_size,
                        'compressed_size': record.compressed_size or '',
                        'checksum': record.checksum or '',
                        'access_count': len(record.access_log),
                        'last_accessed': last_accessed or ''
                    })
            
            logger.info(f"Exported audit trail to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export audit trail: {e}")
            return False
    
    def get_archival_status(self) -> Dict[str, Any]:
        """Get comprehensive archival system status"""
        
        status = {
            "total_records": len(self.records),
            "storage_tiers": {},
            "retention_compliance": {},
            "system_health": "healthy",
            "issues": []
        }
        
        # Analyze by tier
        for tier in ArchivalTier:
            tier_records = [r for r in self.records.values() if r.tier == tier]
            tier_size = sum((r.compressed_size or r.original_size) for r in tier_records)
            
            status["storage_tiers"][tier.value] = {
                "record_count": len(tier_records),
                "total_size_bytes": tier_size,
                "oldest_record": min(r.archived_at for r in tier_records if r.archived_at) if tier_records else None
            }
        
        # Check retention compliance
        current_time = datetime.now()
        expired_count = sum(1 for r in self.records.values() if current_time > r.retention_until)
        
        if expired_count > 0:
            status["system_health"] = "warning"
            status["issues"].append(f"{expired_count} records past retention period")
        
        status["retention_compliance"] = {
            "expired_records": expired_count,
            "total_records": len(self.records),
            "compliance_rate": ((len(self.records) - expired_count) / len(self.records) * 100) if self.records else 100
        }
        
        return status