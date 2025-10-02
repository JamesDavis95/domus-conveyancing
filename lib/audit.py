"""
Audit System - Comprehensive logging for security and compliance
Tracks all user actions, data access, and system events
"""
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
from sqlalchemy.orm import Session

from models import get_db

class AuditEventType(Enum):
    """Types of auditable events"""
    # Authentication & Authorization
    LOGIN = "login"
    LOGOUT = "logout"
    SIGNUP = "signup"
    PERMISSION_DENIED = "permission_denied"
    
    # Project Management
    PROJECT_CREATED = "project_created"
    PROJECT_VIEWED = "project_viewed"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"
    
    # Planning AI
    PLANNING_ANALYSIS = "planning_analysis"
    PRECEDENT_SEARCH = "precedent_search"
    SCENARIO_ANALYSIS = "scenario_analysis"
    
    # Document Management
    DOCUMENT_GENERATED = "document_generated"
    DOCUMENT_DOWNLOADED = "document_downloaded"
    DOCUMENT_VIEWED = "document_viewed"
    BUNDLE_CREATED = "bundle_created"
    
    # Marketplace
    SUPPLY_LISTING_CREATED = "supply_listing_created"
    DEMAND_POST_CREATED = "demand_post_created"
    MARKETPLACE_SEARCH = "marketplace_search"
    MATCH_GENERATED = "match_generated"
    
    # Contracts & Payments
    CONTRACT_CREATED = "contract_created"
    CONTRACT_SIGNED = "contract_signed"
    PAYMENT_PROCESSED = "payment_processed"
    PAYOUT_PROCESSED = "payout_processed"
    
    # Authority Portal
    AUTHORITY_PROJECT_ACCESS = "authority_project_access"
    AUTHORITY_COMMENT = "authority_comment"
    AUTHORITY_DOWNLOAD = "authority_download"
    
    # Admin Actions
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    ORG_UPDATED = "org_updated"
    PLAN_CHANGED = "plan_changed"
    
    # API Usage
    API_REQUEST = "api_request"
    API_ERROR = "api_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    
    # System Events
    DATA_EXPORT = "data_export"
    BACKUP_CREATED = "backup_created"
    ERROR_OCCURRED = "error_occurred"

@dataclass
class AuditEvent:
    """Structured audit event"""
    event_type: AuditEventType
    user_id: Optional[int] = None
    org_id: Optional[int] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        
        # Ensure details is a dict
        if self.details is None:
            self.details = {}

class AuditLogger:
    """Centralized audit logging service"""
    
    def __init__(self):
        # Setup structured logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - AUDIT - %(message)s',
            handlers=[
                logging.FileHandler('audit.log'),
                logging.StreamHandler()  # Also log to console in development
            ]
        )
        self.logger = logging.getLogger('domus_audit')
    
    def log_event(self, event: AuditEvent):
        """Log an audit event"""
        # Convert event to dict for JSON serialization
        event_dict = asdict(event)
        event_dict['timestamp'] = event.timestamp.isoformat()
        event_dict['event_type'] = event.event_type.value
        
        # Log as structured JSON
        self.logger.info(json.dumps(event_dict, default=str))
        
        # TODO: Also store in database for queryable audit trail
        # This would involve creating an AuditLog table and storing events there
    
    def log_auth_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[int] = None,
        org_id: Optional[int] = None,
        success: bool = True,
        details: Optional[Dict] = None,
        request_info: Optional[Dict] = None
    ):
        """Log authentication-related events"""
        event_details = {
            "success": success,
            **(details or {}),
            **(request_info or {})
        }
        
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            org_id=org_id,
            details=event_details,
            ip_address=request_info.get("ip") if request_info else None,
            user_agent=request_info.get("user_agent") if request_info else None
        )
        
        self.log_event(event)
    
    def log_data_access(
        self,
        event_type: AuditEventType,
        user_id: int,
        org_id: int,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict] = None,
        request_info: Optional[Dict] = None
    ):
        """Log data access events"""
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            org_id=org_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=request_info.get("ip") if request_info else None,
            user_agent=request_info.get("user_agent") if request_info else None
        )
        
        self.log_event(event)
    
    def log_business_event(
        self,
        event_type: AuditEventType,
        user_id: int,
        org_id: int,
        details: Dict,
        request_info: Optional[Dict] = None
    ):
        """Log business logic events (payments, contracts, etc.)"""
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            org_id=org_id,
            details=details,
            ip_address=request_info.get("ip") if request_info else None,
            user_agent=request_info.get("user_agent") if request_info else None
        )
        
        self.log_event(event)
    
    def log_authority_access(
        self,
        event_type: AuditEventType,
        token: str,
        project_id: int,
        details: Optional[Dict] = None,
        request_info: Optional[Dict] = None
    ):
        """Log authority portal access (special handling for token-based access)"""
        event_details = {
            "token": token[:8] + "...",  # Only log first 8 chars for security
            "project_id": project_id,
            **(details or {})
        }
        
        event = AuditEvent(
            event_type=event_type,
            resource_type="authority_token",
            details=event_details,
            ip_address=request_info.get("ip") if request_info else None,
            user_agent=request_info.get("user_agent") if request_info else None
        )
        
        self.log_event(event)
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        user_id: Optional[int] = None,
        org_id: Optional[int] = None,
        details: Optional[Dict] = None,
        request_info: Optional[Dict] = None
    ):
        """Log error events"""
        event_details = {
            "error_type": error_type,
            "error_message": error_message,
            **(details or {})
        }
        
        event = AuditEvent(
            event_type=AuditEventType.ERROR_OCCURRED,
            user_id=user_id,
            org_id=org_id,
            details=event_details,
            ip_address=request_info.get("ip") if request_info else None,
            user_agent=request_info.get("user_agent") if request_info else None
        )
        
        self.log_event(event)

# Global audit logger instance
audit_logger = AuditLogger()

# Convenience functions for common audit scenarios
def audit_login(user_id: int, org_id: int, success: bool = True, request_info: Dict = None):
    """Audit user login"""
    audit_logger.log_auth_event(
        AuditEventType.LOGIN,
        user_id=user_id,
        org_id=org_id,
        success=success,
        request_info=request_info
    )

def audit_project_access(user_id: int, org_id: int, project_id: int, action: str, request_info: Dict = None):
    """Audit project access"""
    event_type = AuditEventType.PROJECT_VIEWED if action == "view" else AuditEventType.PROJECT_UPDATED
    audit_logger.log_data_access(
        event_type,
        user_id=user_id,
        org_id=org_id,
        resource_type="project",
        resource_id=project_id,
        request_info=request_info
    )

def audit_document_generation(user_id: int, org_id: int, project_id: int, doc_type: str, request_info: Dict = None):
    """Audit document generation"""
    audit_logger.log_data_access(
        AuditEventType.DOCUMENT_GENERATED,
        user_id=user_id,
        org_id=org_id,
        resource_type="document",
        details={"project_id": project_id, "document_type": doc_type},
        request_info=request_info
    )

def audit_planning_analysis(user_id: int, org_id: int, project_id: int, analysis_type: str, request_info: Dict = None):
    """Audit planning AI analysis"""
    audit_logger.log_data_access(
        AuditEventType.PLANNING_ANALYSIS,
        user_id=user_id,
        org_id=org_id,
        resource_type="analysis",
        details={"project_id": project_id, "analysis_type": analysis_type},
        request_info=request_info
    )

def audit_authority_access(token: str, project_id: int, action: str, request_info: Dict = None):
    """Audit authority portal access"""
    event_type_map = {
        "view": AuditEventType.AUTHORITY_PROJECT_ACCESS,
        "comment": AuditEventType.AUTHORITY_COMMENT,
        "download": AuditEventType.AUTHORITY_DOWNLOAD
    }
    
    event_type = event_type_map.get(action, AuditEventType.AUTHORITY_PROJECT_ACCESS)
    audit_logger.log_authority_access(
        event_type,
        token=token,
        project_id=project_id,
        details={"action": action},
        request_info=request_info
    )

def audit_marketplace_activity(user_id: int, org_id: int, activity_type: str, details: Dict, request_info: Dict = None):
    """Audit marketplace activity"""
    event_type_map = {
        "supply_created": AuditEventType.SUPPLY_LISTING_CREATED,
        "demand_created": AuditEventType.DEMAND_POST_CREATED,
        "search": AuditEventType.MARKETPLACE_SEARCH,
        "match": AuditEventType.MATCH_GENERATED
    }
    
    event_type = event_type_map.get(activity_type, AuditEventType.MARKETPLACE_SEARCH)
    audit_logger.log_business_event(
        event_type,
        user_id=user_id,
        org_id=org_id,
        details=details,
        request_info=request_info
    )

def audit_contract_event(user_id: int, org_id: int, contract_id: int, event: str, details: Dict, request_info: Dict = None):
    """Audit contract-related events"""
    event_type_map = {
        "created": AuditEventType.CONTRACT_CREATED,
        "signed": AuditEventType.CONTRACT_SIGNED,
        "payment": AuditEventType.PAYMENT_PROCESSED,
        "payout": AuditEventType.PAYOUT_PROCESSED
    }
    
    event_type = event_type_map.get(event, AuditEventType.CONTRACT_CREATED)
    audit_details = {"contract_id": contract_id, **details}
    
    audit_logger.log_business_event(
        event_type,
        user_id=user_id,
        org_id=org_id,
        details=audit_details,
        request_info=request_info
    )

def audit_quota_exceeded(user_id: int, org_id: int, quota_type: str, current_usage: int, limit: int, request_info: Dict = None):
    """Audit quota exceeded events"""
    audit_logger.log_business_event(
        AuditEventType.QUOTA_EXCEEDED,
        user_id=user_id,
        org_id=org_id,
        details={
            "quota_type": quota_type,
            "current_usage": current_usage,
            "limit": limit
        },
        request_info=request_info
    )

def audit_permission_denied(user_id: int, org_id: int, feature: str, role: str, request_info: Dict = None):
    """Audit permission denied events"""
    audit_logger.log_auth_event(
        AuditEventType.PERMISSION_DENIED,
        user_id=user_id,
        org_id=org_id,
        success=False,
        details={"feature": feature, "role": role},
        request_info=request_info
    )