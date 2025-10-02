"""
Quota Middleware - Plan-based usage limitations
Enforces subscription plan quotas and tracks usage
"""
from typing import Dict, Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from lib.permissions import PlanType, PLAN_QUOTAS, check_quota_limit, get_quota_info
from models import get_db, Users, Orgs, Projects, Documents, MarketplaceSupply, MarketplaceDemand, Contracts, UsageCounters
from auth_system import get_current_user

class QuotaMiddleware:
    """Middleware for enforcing plan-based quotas"""
    
    @staticmethod
    async def check_quota(
        quota_type: str,
        user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> Dict:
        """
        Check if user has quota available for the specified action
        Returns quota information
        """
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Get organization plan
        org = db.query(Orgs).filter(Orgs.id == user["org_id"]).first()
        if not org:
            raise HTTPException(status_code=401, detail="Organization not found")
        
        # Get current usage for this month
        current_usage = await QuotaMiddleware._get_current_usage(db, user["org_id"], quota_type)
        
        # Check quota limit
        if not check_quota_limit(org.plan, quota_type, current_usage):
            quota_info = get_quota_info(org.plan, quota_type, current_usage)
            raise HTTPException(
                status_code=402,  # Payment Required
                detail={
                    "error": "Quota exceeded",
                    "quota_type": quota_type,
                    "current_usage": current_usage,
                    "limit": quota_info["limit"],
                    "plan": org.plan.value,
                    "message": f"You've reached your {quota_type} limit for your {org.plan.value} plan. Please upgrade to continue."
                }
            )
        
        return get_quota_info(org.plan, quota_type, current_usage)
    
    @staticmethod
    async def _get_current_usage(db: Session, org_id: int, quota_type: str) -> int:
        """Get current usage count for the organization this month"""
        
        # Get start of current month
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        if quota_type == "projects":
            # Count projects created this month
            return db.query(func.count(Projects.id)).filter(
                Projects.org_id == org_id,
                Projects.created_at >= month_start
            ).scalar() or 0
            
        elif quota_type == "docs":
            # Count documents generated this month
            return db.query(func.count(Documents.id)).filter(
                Documents.org_id == org_id,
                Documents.created_at >= month_start
            ).scalar() or 0
            
        elif quota_type == "marketplace_posts":
            # Count marketplace posts (supply + demand) this month
            supply_count = db.query(func.count(MarketplaceSupply.id)).filter(
                MarketplaceSupply.org_id == org_id,
                MarketplaceSupply.created_at >= month_start
            ).scalar() or 0
            
            demand_count = db.query(func.count(MarketplaceDemand.id)).filter(
                MarketplaceDemand.org_id == org_id,
                MarketplaceDemand.created_at >= month_start
            ).scalar() or 0
            
            return supply_count + demand_count
            
        elif quota_type == "contracts":
            # Count contracts this month (where org is buyer or seller)
            return db.query(func.count(Contracts.id)).filter(
                ((Contracts.buyer_org_id == org_id) | (Contracts.seller_org_id == org_id)),
                Contracts.created_at >= month_start
            ).scalar() or 0
        
        return 0
    
    @staticmethod
    async def increment_usage(
        db: Session,
        org_id: int,
        quota_type: str,
        amount: int = 1
    ):
        """
        Increment usage counter for quota tracking
        This should be called after successful creation of quota-limited resources
        """
        now = datetime.utcnow()
        
        # Find or create usage counter for this month
        usage_counter = db.query(UsageCounters).filter(
            UsageCounters.org_id == org_id,
            UsageCounters.quota_type == quota_type,
            UsageCounters.period_start <= now,
            UsageCounters.period_end > now
        ).first()
        
        if not usage_counter:
            # Create new counter for this month
            month_start = datetime(now.year, now.month, 1)
            next_month = month_start + timedelta(days=32)
            month_end = datetime(next_month.year, next_month.month, 1)
            
            usage_counter = UsageCounters(
                org_id=org_id,
                quota_type=quota_type,
                usage_count=amount,
                period_start=month_start,
                period_end=month_end
            )
            db.add(usage_counter)
        else:
            usage_counter.usage_count += amount
            usage_counter.last_updated = now
        
        db.commit()

# Convenience decorators for common quota checks
def require_projects_quota():
    """Decorator to check projects quota before endpoint execution"""
    async def quota_dependency(
        user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        await QuotaMiddleware.check_quota("projects", user, db)
        return user
    return quota_dependency

def require_docs_quota():
    """Decorator to check documents quota before endpoint execution"""
    async def quota_dependency(
        user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        await QuotaMiddleware.check_quota("docs", user, db)
        return user
    return quota_dependency

def require_marketplace_quota():
    """Decorator to check marketplace posts quota before endpoint execution"""
    async def quota_dependency(
        user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        await QuotaMiddleware.check_quota("marketplace_posts", user, db)
        return user
    return quota_dependency

def require_contracts_quota():
    """Decorator to check contracts quota before endpoint execution"""
    async def quota_dependency(
        user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        await QuotaMiddleware.check_quota("contracts", user, db)
        return user
    return quota_dependency

# Usage tracking helpers
async def track_project_creation(db: Session, org_id: int):
    """Track project creation for quota"""
    await QuotaMiddleware.increment_usage(db, org_id, "projects")

async def track_document_generation(db: Session, org_id: int):
    """Track document generation for quota"""
    await QuotaMiddleware.increment_usage(db, org_id, "docs")

async def track_marketplace_post(db: Session, org_id: int):
    """Track marketplace post for quota"""
    await QuotaMiddleware.increment_usage(db, org_id, "marketplace_posts")

async def track_contract_creation(db: Session, org_id: int):
    """Track contract creation for quota"""
    await QuotaMiddleware.increment_usage(db, org_id, "contracts")

# Get usage information for display
async def get_org_usage_summary(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get comprehensive usage summary for organization
    Used for dashboard and usage displays
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    org = db.query(Orgs).filter(Orgs.id == user["org_id"]).first()
    if not org:
        raise HTTPException(status_code=401, detail="Organization not found")
    
    quota_types = ["projects", "docs", "marketplace_posts", "contracts"]
    usage_summary = {}
    
    for quota_type in quota_types:
        current_usage = await QuotaMiddleware._get_current_usage(db, user["org_id"], quota_type)
        quota_info = get_quota_info(org.plan, quota_type, current_usage)
        usage_summary[quota_type] = quota_info
    
    return {
        "org_id": org.id,
        "org_name": org.name,
        "plan": org.plan.value,
        "quotas": usage_summary,
        "period": "monthly"  # All quotas are monthly
    }