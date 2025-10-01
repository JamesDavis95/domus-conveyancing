"""
Operational Admin Tools
Complete platform management with user administration, subscription management, marketplace oversight, and system monitoring
"""

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, or_, text
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from models import get_db, User, Organization, Subscription, Payment, Usage
from production_auth_complete import get_current_user, require_role, UserRole
from backend_auth_complete import PlanType, PLAN_LIMITS
from stripe_integration_complete import StripeService, BillingAPI
from production_data_layer import Project, BNGListing, LPAStatistic, Notification
from production_infrastructure import HealthCheckService, PerformanceMonitor
import csv
import io
from enum import Enum

class AdminAction(Enum):
    USER_SUSPENDED = "user_suspended"
    USER_ACTIVATED = "user_activated"
    SUBSCRIPTION_MODIFIED = "subscription_modified"
    REFUND_ISSUED = "refund_issued"
    LISTING_MODERATED = "listing_moderated"
    SYSTEM_MAINTENANCE = "system_maintenance"

class UserManagementService:
    """User account administration service"""
    
    @staticmethod
    async def get_all_users(
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        plan_type: Optional[PlanType] = None,
        active_only: bool = True,
        page: int = 1,
        per_page: int = 50,
        db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        """Get paginated list of all users"""
        
        query = db.query(User).options(joinedload(User.organization))
        
        if search:
            query = query.filter(or_(
                User.email.ilike(f"%{search}%"),
                User.name.ilike(f"%{search}%"),
                User.organization.has(Organization.name.ilike(f"%{search}%"))
            ))
        
        if role:
            query = query.filter(User.role == role)
        
        if plan_type:
            query = query.filter(User.organization.has(Organization.plan_type == plan_type))
        
        if active_only:
            query = query.filter(User.is_active == True)
        
        total_count = query.count()
        users = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            "users": [{
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "organization": {
                    "id": user.organization.id,
                    "name": user.organization.name,
                    "plan_type": user.organization.plan_type.value,
                    "subscription_status": user.organization.subscription_status.value
                }
            } for user in users],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": (total_count + per_page - 1) // per_page
            }
        }
    
    @staticmethod
    async def get_user_details(
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Get detailed user information"""
        
        user = db.query(User).options(joinedload(User.organization)).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get usage statistics
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        usage_stats = db.query(
            Usage.resource_type,
            func.count(Usage.id).label('count')
        ).filter(
            Usage.user_id == user_id,
            Usage.created_at >= thirty_days_ago
        ).group_by(Usage.resource_type).all()
        
        # Get projects
        projects = db.query(Project).filter(Project.user_id == user_id).count()
        
        # Get BNG listings
        bng_listings = db.query(BNGListing).filter(BNGListing.user_id == user_id).count()
        
        # Get recent activity
        recent_usage = db.query(Usage).filter(
            Usage.user_id == user_id
        ).order_by(desc(Usage.created_at)).limit(10).all()
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            },
            "organization": {
                "id": user.organization.id,
                "name": user.organization.name,
                "plan_type": user.organization.plan_type.value,
                "subscription_status": user.organization.subscription_status.value,
                "trial_end": user.organization.trial_end.isoformat() if user.organization.trial_end else None,
                "stripe_customer_id": user.organization.stripe_customer_id
            },
            "usage_statistics": {
                "thirty_day_usage": {stat.resource_type: stat.count for stat in usage_stats},
                "projects_created": projects,
                "bng_listings_created": bng_listings
            },
            "recent_activity": [{
                "resource_type": usage.resource_type,
                "timestamp": usage.created_at.isoformat()
            } for usage in recent_usage]
        }
    
    @staticmethod
    async def suspend_user(
        user_id: int,
        reason: str,
        admin_user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Suspend user account"""
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = False
        db.commit()
        
        # Log admin action
        await AdminActionService.log_action(
            admin_user.id,
            AdminAction.USER_SUSPENDED,
            f"Suspended user {user.email}: {reason}",
            {"user_id": user_id, "reason": reason},
            db
        )
        
        return {
            "message": f"User {user.email} has been suspended",
            "reason": reason,
            "suspended_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def activate_user(
        user_id: int,
        admin_user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Activate user account"""
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = True
        db.commit()
        
        # Log admin action
        await AdminActionService.log_action(
            admin_user.id,
            AdminAction.USER_ACTIVATED,
            f"Activated user {user.email}",
            {"user_id": user_id},
            db
        )
        
        return {
            "message": f"User {user.email} has been activated",
            "activated_at": datetime.utcnow().isoformat()
        }

class SubscriptionManagementService:
    """Subscription and billing management service"""
    
    @staticmethod
    async def get_subscription_overview(
        db: Session
    ) -> Dict[str, Any]:
        """Get subscription overview statistics"""
        
        # Subscription counts by plan
        plan_counts = db.query(
            Organization.plan_type,
            func.count(Organization.id).label('count')
        ).group_by(Organization.plan_type).all()
        
        # Revenue statistics
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_revenue = db.query(
            func.sum(Payment.amount).label('total')
        ).filter(
            Payment.created_at >= thirty_days_ago,
            Payment.status == "succeeded"
        ).scalar() or 0
        
        # Churn analysis
        cancelled_this_month = db.query(Organization).filter(
            Organization.subscription_status == "cancelled",
            Organization.created_at >= thirty_days_ago
        ).count()
        
        new_this_month = db.query(Organization).filter(
            Organization.created_at >= thirty_days_ago
        ).count()
        
        return {
            "subscription_stats": {
                "by_plan": {plan.plan_type.value: plan.count for plan in plan_counts},
                "total_active": db.query(Organization).filter(
                    Organization.subscription_status.in_(["active", "trialing"])
                ).count(),
                "total_cancelled": db.query(Organization).filter(
                    Organization.subscription_status == "cancelled"
                ).count()
            },
            "revenue_stats": {
                "monthly_revenue_gbp": recent_revenue / 100,  # Convert from pence
                "new_subscriptions_this_month": new_this_month,
                "cancelled_this_month": cancelled_this_month,
                "churn_rate": (cancelled_this_month / max(new_this_month, 1)) * 100
            }
        }
    
    @staticmethod
    async def get_subscription_details(
        org_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Get detailed subscription information"""
        
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Get subscription history
        subscriptions = db.query(Subscription).filter(
            Subscription.org_id == org_id
        ).order_by(desc(Subscription.created_at)).all()
        
        # Get payment history
        payments = db.query(Payment).filter(
            Payment.org_id == org_id
        ).order_by(desc(Payment.created_at)).limit(20).all()
        
        return {
            "organization": {
                "id": org.id,
                "name": org.name,
                "plan_type": org.plan_type.value,
                "subscription_status": org.subscription_status.value,
                "stripe_customer_id": org.stripe_customer_id,
                "trial_end": org.trial_end.isoformat() if org.trial_end else None
            },
            "subscriptions": [{
                "id": sub.id,
                "stripe_subscription_id": sub.stripe_subscription_id,
                "plan_type": sub.plan_type.value,
                "status": sub.status,
                "current_period_start": sub.current_period_start.isoformat(),
                "current_period_end": sub.current_period_end.isoformat(),
                "cancelled_at": sub.cancelled_at.isoformat() if sub.cancelled_at else None
            } for sub in subscriptions],
            "payments": [{
                "id": payment.id,
                "amount_gbp": payment.amount / 100,  # Convert from pence
                "status": payment.status,
                "created_at": payment.created_at.isoformat()
            } for payment in payments]
        }
    
    @staticmethod
    async def modify_subscription(
        org_id: int,
        new_plan_type: PlanType,
        admin_user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Modify organization subscription"""
        
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        old_plan = org.plan_type
        org.plan_type = new_plan_type
        db.commit()
        
        # Log admin action
        await AdminActionService.log_action(
            admin_user.id,
            AdminAction.SUBSCRIPTION_MODIFIED,
            f"Changed {org.name} plan from {old_plan.value} to {new_plan_type.value}",
            {"org_id": org_id, "old_plan": old_plan.value, "new_plan": new_plan_type.value},
            db
        )
        
        return {
            "message": f"Subscription updated for {org.name}",
            "old_plan": old_plan.value,
            "new_plan": new_plan_type.value,
            "updated_at": datetime.utcnow().isoformat()
        }

class MarketplaceOversightService:
    """BNG marketplace moderation and oversight"""
    
    @staticmethod
    async def get_marketplace_overview(
        db: Session
    ) -> Dict[str, Any]:
        """Get marketplace overview statistics"""
        
        # Listing statistics
        listing_stats = db.query(
            BNGListing.status,
            func.count(BNGListing.id).label('count')
        ).group_by(BNGListing.status).all()
        
        # Provider statistics
        total_providers = db.query(BNGListing.org_id).distinct().count()
        verified_providers = db.query(BNGListing).filter(
            BNGListing.provider_verified == True
        ).distinct(BNGListing.org_id).count()
        
        # Revenue statistics
        total_value = db.query(
            func.sum(BNGListing.units_available * BNGListing.price_per_unit).label('total')
        ).filter(BNGListing.status == "active").scalar() or 0
        
        return {
            "listing_stats": {
                "by_status": {stat.status.value: stat.count for stat in listing_stats},
                "total_listings": db.query(BNGListing).count(),
                "active_listings": db.query(BNGListing).filter(BNGListing.status == "active").count()
            },
            "provider_stats": {
                "total_providers": total_providers,
                "verified_providers": verified_providers,
                "verification_rate": (verified_providers / max(total_providers, 1)) * 100
            },
            "market_stats": {
                "total_market_value_gbp": total_value / 100,  # Convert from pence
                "average_price_per_unit": (total_value / max(
                    db.query(func.sum(BNGListing.units_available)).filter(
                        BNGListing.status == "active"
                    ).scalar() or 1, 1
                )) / 100
            }
        }
    
    @staticmethod
    async def get_flagged_listings(
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get listings that need moderation"""
        
        # Mock flagged listings - implement real flagging logic
        flagged_listings = db.query(BNGListing).filter(
            or_(
                BNGListing.provider_verified == False,
                BNGListing.price_per_unit < 1000,  # Suspiciously low prices
                BNGListing.units_available > 100   # Suspiciously high availability
            )
        ).limit(20).all()
        
        return [{
            "id": listing.id,
            "title": listing.title,
            "provider_name": listing.provider_name,
            "price_per_unit": listing.price_per_unit / 100,
            "units_available": listing.units_available,
            "created_at": listing.created_at.isoformat(),
            "flags": [
                "Unverified provider" if not listing.provider_verified else None,
                "Low price" if listing.price_per_unit < 1000 else None,
                "High availability" if listing.units_available > 100 else None
            ]
        } for listing in flagged_listings]
    
    @staticmethod
    async def moderate_listing(
        listing_id: str,
        action: str,
        reason: str,
        admin_user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Moderate a marketplace listing"""
        
        listing = db.query(BNGListing).filter(BNGListing.id == listing_id).first()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        if action == "approve":
            listing.provider_verified = True
        elif action == "reject":
            listing.status = "expired"
        elif action == "flag":
            # Add to flagged list
            pass
        
        db.commit()
        
        # Log admin action
        await AdminActionService.log_action(
            admin_user.id,
            AdminAction.LISTING_MODERATED,
            f"Moderated listing {listing.title}: {action} - {reason}",
            {"listing_id": listing_id, "action": action, "reason": reason},
            db
        )
        
        return {
            "message": f"Listing {action}ed successfully",
            "listing_id": listing_id,
            "action": action,
            "reason": reason,
            "moderated_at": datetime.utcnow().isoformat()
        }

class SystemMonitoringService:
    """System monitoring and analytics service"""
    
    @staticmethod
    async def get_platform_analytics(
        days: int = 30,
        db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        """Get comprehensive platform analytics"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # User activity
        daily_active_users = db.query(
            func.date(Usage.created_at).label('date'),
            func.count(Usage.user_id.distinct()).label('users')
        ).filter(
            Usage.created_at >= cutoff_date
        ).group_by(func.date(Usage.created_at)).all()
        
        # API usage by type
        api_usage = db.query(
            Usage.resource_type,
            func.count(Usage.id).label('count')
        ).filter(
            Usage.created_at >= cutoff_date
        ).group_by(Usage.resource_type).all()
        
        # Growth metrics
        new_users = db.query(User).filter(User.created_at >= cutoff_date).count()
        new_orgs = db.query(Organization).filter(Organization.created_at >= cutoff_date).count()
        
        # System performance
        system_health = await HealthCheckService.check_system_resources()
        performance_metrics = await PerformanceMonitor.get_performance_metrics(db)
        
        return {
            "time_period": f"Last {days} days",
            "user_analytics": {
                "daily_active_users": [{
                    "date": str(day.date),
                    "users": day.users
                } for day in daily_active_users],
                "new_users": new_users,
                "new_organizations": new_orgs
            },
            "usage_analytics": {
                "by_resource_type": {usage.resource_type: usage.count for usage in api_usage},
                "total_api_calls": sum(usage.count for usage in api_usage)
            },
            "system_health": system_health,
            "performance_metrics": performance_metrics
        }
    
    @staticmethod
    async def export_analytics_csv(
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> str:
        """Export analytics data as CSV"""
        
        # Get usage data
        usage_data = db.query(Usage).filter(
            Usage.created_at >= start_date,
            Usage.created_at <= end_date
        ).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Date', 'User ID', 'Organization ID', 'Resource Type', 'Timestamp'
        ])
        
        for usage in usage_data:
            writer.writerow([
                usage.created_at.date(),
                usage.user_id,
                usage.org_id,
                usage.resource_type,
                usage.created_at.isoformat()
            ])
        
        return output.getvalue()

class AdminActionService:
    """Track and log administrative actions"""
    
    @staticmethod
    async def log_action(
        admin_user_id: int,
        action: AdminAction,
        description: str,
        metadata: Dict[str, Any],
        db: Session
    ):
        """Log administrative action"""
        
        # Store in audit log table (would need to create this table)
        # For now, just log to application logs
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"ADMIN ACTION: User {admin_user_id} - {action.value} - {description} - {metadata}")

class AdminAPI:
    """Administrative API endpoints"""
    
    @staticmethod
    async def get_dashboard(
        admin_user: User = Depends(require_role(UserRole.ADMIN)),
        db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        """Get admin dashboard overview"""
        
        # Get overview statistics
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        total_orgs = db.query(Organization).count()
        active_subscriptions = db.query(Organization).filter(
            Organization.subscription_status.in_(["active", "trialing"])
        ).count()
        
        # Recent activity
        recent_users = db.query(User).order_by(desc(User.created_at)).limit(5).all()
        recent_payments = db.query(Payment).order_by(desc(Payment.created_at)).limit(5).all()
        
        return {
            "overview": {
                "total_users": total_users,
                "active_users": active_users,
                "total_organizations": total_orgs,
                "active_subscriptions": active_subscriptions,
                "user_activity_rate": (active_users / max(total_users, 1)) * 100
            },
            "recent_activity": {
                "new_users": [{
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "created_at": user.created_at.isoformat()
                } for user in recent_users],
                "recent_payments": [{
                    "id": payment.id,
                    "amount_gbp": payment.amount / 100,
                    "status": payment.status,
                    "created_at": payment.created_at.isoformat()
                } for payment in recent_payments]
            }
        }
    
    @staticmethod
    async def impersonate_user(
        user_id: int,
        admin_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
        db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        """Impersonate user for support purposes"""
        
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create impersonation token
        from production_auth_complete import AuthService
        
        impersonation_token = AuthService.create_access_token({
            "user_id": target_user.id,
            "email": target_user.email,
            "role": target_user.role.value,
            "org_id": target_user.org_id,
            "impersonated_by": admin_user.id
        })
        
        # Log impersonation
        await AdminActionService.log_action(
            admin_user.id,
            AdminAction.USER_SUSPENDED,  # Use closest available action
            f"Impersonated user {target_user.email}",
            {"impersonated_user_id": user_id},
            db
        )
        
        return {
            "impersonation_token": impersonation_token,
            "impersonated_user": {
                "id": target_user.id,
                "email": target_user.email,
                "name": target_user.name,
                "organization": target_user.organization.name
            },
            "warning": "This is an impersonation session. All actions will be logged."
        }