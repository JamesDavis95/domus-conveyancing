"""
Premium Pricing Structure
Implements 4-tier pricing with credits system and marketplace fee    ENTERPRISE = PricingTier(
        name="Enterprise",
        price_monthly=2083.33,  # £25k/year ÷ 12 months
        price_yearly=25000.00,  # £25k/year (starter price)
        currency="GBP",
        description="White-label solution with dedicated support",
        features=[
            "Unlimited projects",
            "Unlimited API calls", 
            "White-label branding",
            "Dedicated support",
            "Custom integrations",
            "SLA guarantees",
            "Priority processing"
        ],
        quotas=PricingQuotas(
            api_calls_monthly=2000,    # Updated from 200 to 2000
            projects_total=10,
            ai_analyses_monthly=20,
            document_generations_monthly=8,
            submission_packs_monthly=4,
            marketplace_listings=50
        )num import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

class PlanType(str, Enum):
    """Subscription plan types"""
    FREE = "FREE"
    DEV = "DEV"
    DEV_PRO = "DEV_PRO"
    CONSULTANT = "CONSULTANT"
    ENTERPRISE = "ENTERPRISE"

class CreditType(str, Enum):
    """Types of credits available for purchase"""
    AI_ANALYSIS = "AI_ANALYSIS"
    AUTO_DOCS = "AUTO_DOCS"
    SUBMISSION_BUNDLES = "SUBMISSION_BUNDLES"

@dataclass
class PlanLimits:
    """Plan limitations and quotas"""
    max_projects: Optional[int]  # None = unlimited
    ai_analyses_monthly: int
    auto_docs_monthly: int
    submission_bundles_monthly: int
    advanced_docs: bool = False
    appeals_objections: bool = False
    full_analytics: bool = False
    marketplace_access: str = "none"  # none, demand, supply, both
    custom_ai_training: bool = False
    dedicated_infra: bool = False
    sso_sla: bool = False

@dataclass
class PlanPricing:
    """Plan pricing information"""
    monthly_price_gbp: int
    annual_price_gbp: Optional[int] = None
    per_seat: bool = True
    currency: str = "GBP"
    stripe_price_id: Optional[str] = None
    stripe_annual_price_id: Optional[str] = None

@dataclass
class CreditPack:
    """Credit pack pricing"""
    quantity: int
    price_gbp: int
    credit_type: CreditType
    stripe_price_id: Optional[str] = None

class PricingConfig:
    """Centralized pricing configuration"""
    
    # Plan limits configuration
    PLAN_LIMITS = {
        PlanType.FREE: PlanLimits(
            max_projects=0,
            ai_analyses_monthly=0,
            auto_docs_monthly=0,
            submission_bundles_monthly=0,
            marketplace_access="supply"  # Landowners can list for free
        ),
        PlanType.DEV: PlanLimits(
            max_projects=2,
            ai_analyses_monthly=5,
            auto_docs_monthly=2,
            submission_bundles_monthly=1,
            marketplace_access="demand"
        ),
        PlanType.DEV_PRO: PlanLimits(
            max_projects=10,
            ai_analyses_monthly=20,
            auto_docs_monthly=8,
            submission_bundles_monthly=4,
            marketplace_access="demand"
        ),
        PlanType.CONSULTANT: PlanLimits(
            max_projects=None,  # Unlimited
            ai_analyses_monthly=40,
            auto_docs_monthly=25,
            submission_bundles_monthly=12,
            advanced_docs=True,
            appeals_objections=True,
            full_analytics=True,
            marketplace_access="demand"
        ),
        PlanType.ENTERPRISE: PlanLimits(
            max_projects=None,  # Unlimited
            ai_analyses_monthly=999999,  # Effectively unlimited
            auto_docs_monthly=999999,
            submission_bundles_monthly=999999,
            advanced_docs=True,
            appeals_objections=True,
            full_analytics=True,
            marketplace_access="both",
            custom_ai_training=True,
            dedicated_infra=True,
            sso_sla=True
        )
    }
    
    # Plan pricing configuration
    PLAN_PRICING = {
        PlanType.FREE: PlanPricing(
            monthly_price_gbp=0,
            per_seat=False
        ),
        PlanType.DEV: PlanPricing(
            monthly_price_gbp=199,
            annual_price_gbp=1990,  # ~17% discount
            stripe_price_id="price_dev_monthly",
            stripe_annual_price_id="price_dev_annual"
        ),
        PlanType.DEV_PRO: PlanPricing(
            monthly_price_gbp=399,
            annual_price_gbp=3990,  # ~17% discount
            stripe_price_id="price_dev_pro_monthly",
            stripe_annual_price_id="price_dev_pro_annual"
        ),
        PlanType.CONSULTANT: PlanPricing(
            monthly_price_gbp=999,
            annual_price_gbp=9990,  # ~17% discount
            stripe_price_id="price_consultant_monthly",
            stripe_annual_price_id="price_consultant_annual"
        ),
        PlanType.ENTERPRISE: PlanPricing(
            monthly_price_gbp=2083,  # £25k/year
            annual_price_gbp=25000,
            stripe_price_id="price_enterprise_monthly",
            stripe_annual_price_id="price_enterprise_annual"
        )
    }
    
    # Credit pack pricing
    CREDIT_PACKS = {
        CreditType.AI_ANALYSIS: CreditPack(
            quantity=10,
            price_gbp=400,
            credit_type=CreditType.AI_ANALYSIS,
            stripe_price_id="price_ai_credits_10"
        ),
        CreditType.AUTO_DOCS: CreditPack(
            quantity=10,
            price_gbp=1000,
            credit_type=CreditType.AUTO_DOCS,
            stripe_price_id="price_docs_credits_10"
        ),
        CreditType.SUBMISSION_BUNDLES: CreditPack(
            quantity=10,
            price_gbp=1000,
            credit_type=CreditType.SUBMISSION_BUNDLES,
            stripe_price_id="price_bundle_credits_10"
        )
    }
    
    # Marketplace fees
    MARKETPLACE_CONFIG = {
        "fee_percentage": 5.0,  # 5% total (2.5% buyer + 2.5% seller)
        "buyer_fee_percentage": 2.5,
        "seller_fee_percentage": 2.5,
        "escrow_fee_gbp": 50,  # Paid by buyer
        "min_transaction_gbp": 1000,
        "max_transaction_gbp": 10000000
    }

    @classmethod
    def get_plan_limits(cls, plan: PlanType) -> PlanLimits:
        """Get limits for a specific plan"""
        return cls.PLAN_LIMITS.get(plan, cls.PLAN_LIMITS[PlanType.FREE])
    
    @classmethod
    def get_plan_pricing(cls, plan: PlanType) -> PlanPricing:
        """Get pricing for a specific plan"""
        return cls.PLAN_PRICING.get(plan, cls.PLAN_PRICING[PlanType.FREE])
    
    @classmethod
    def get_credit_pack(cls, credit_type: CreditType) -> CreditPack:
        """Get credit pack pricing"""
        return cls.CREDIT_PACKS.get(credit_type)
    
    @classmethod
    def can_access_feature(cls, plan: PlanType, feature: str) -> bool:
        """Check if plan can access specific feature"""
        limits = cls.get_plan_limits(plan)
        
        feature_checks = {
            "projects": limits.max_projects is None or limits.max_projects > 0,
            "planning_ai": limits.ai_analyses_monthly > 0,
            "auto_docs": limits.auto_docs_monthly > 0,
            "submission_pack": limits.submission_bundles_monthly > 0,
            "advanced_docs": limits.advanced_docs,
            "appeals_objections": limits.appeals_objections,
            "full_analytics": limits.full_analytics,
            "marketplace_demand": limits.marketplace_access in ["demand", "both"],
            "marketplace_supply": limits.marketplace_access in ["supply", "both"],
            "custom_ai_training": limits.custom_ai_training,
            "dedicated_infra": limits.dedicated_infra,
            "sso_sla": limits.sso_sla
        }
        
        return feature_checks.get(feature, False)
    
    @classmethod
    def calculate_marketplace_fees(cls, transaction_amount_gbp: float) -> Dict[str, float]:
        """Calculate marketplace fees for a transaction"""
        config = cls.MARKETPLACE_CONFIG
        
        if transaction_amount_gbp < config["min_transaction_gbp"]:
            raise ValueError(f"Transaction amount below minimum {config['min_transaction_gbp']}")
        
        if transaction_amount_gbp > config["max_transaction_gbp"]:
            raise ValueError(f"Transaction amount above maximum {config['max_transaction_gbp']}")
        
        buyer_fee = transaction_amount_gbp * (config["buyer_fee_percentage"] / 100)
        seller_fee = transaction_amount_gbp * (config["seller_fee_percentage"] / 100)
        escrow_fee = config["escrow_fee_gbp"]
        
        total_buyer_cost = transaction_amount_gbp + buyer_fee + escrow_fee
        seller_receives = transaction_amount_gbp - seller_fee
        
        return {
            "transaction_amount": transaction_amount_gbp,
            "buyer_fee": buyer_fee,
            "seller_fee": seller_fee,
            "escrow_fee": escrow_fee,
            "total_buyer_cost": total_buyer_cost,
            "seller_receives": seller_receives,
            "platform_revenue": buyer_fee + seller_fee + escrow_fee
        }

class QuotaManager:
    """Manages monthly quotas and credits"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def check_quota(self, org_id: str, feature: str) -> Dict[str, Any]:
        """Check if organization has quota remaining for feature"""
        # This would integrate with your existing usage_counters table
        # For now, return a structure that can be implemented
        
        quota_check = {
            "has_quota": True,
            "remaining": 10,
            "limit": 20,
            "reset_date": "2025-11-01",
            "can_buy_credits": True
        }
        
        logger.info(f"Quota check for org {org_id}, feature {feature}: {quota_check}")
        return quota_check
    
    async def consume_quota(self, org_id: str, feature: str, amount: int = 1) -> bool:
        """Consume quota for a feature usage"""
        # This would decrement the usage counter
        logger.info(f"Consuming {amount} {feature} quota for org {org_id}")
        return True
    
    async def add_credits(self, org_id: str, credit_type: CreditType, amount: int) -> bool:
        """Add credits to organization"""
        logger.info(f"Adding {amount} {credit_type} credits to org {org_id}")
        return True
    
    async def get_usage_summary(self, org_id: str) -> Dict[str, Any]:
        """Get comprehensive usage summary for organization"""
        return {
            "current_plan": PlanType.DEV,
            "billing_cycle_start": "2025-10-01",
            "billing_cycle_end": "2025-10-31",
            "quotas": {
                "ai_analyses": {"used": 3, "limit": 5, "remaining": 2},
                "auto_docs": {"used": 1, "limit": 2, "remaining": 1},
                "submission_bundles": {"used": 0, "limit": 1, "remaining": 1},
                "projects": {"used": 2, "limit": 2, "remaining": 0}
            },
            "credits": {
                "ai_analyses": 5,
                "auto_docs": 0,
                "submission_bundles": 2
            }
        }

def format_price_display(price_gbp: int, currency: str = "GBP") -> str:
    """Format price for display"""
    if currency == "GBP":
        return f"£{price_gbp:,}"
    return f"{price_gbp:,} {currency}"

def get_plan_display_name(plan: PlanType) -> str:
    """Get human-readable plan name"""
    names = {
        PlanType.FREE: "Landowner",
        PlanType.DEV: "Developer", 
        PlanType.DEV_PRO: "Developer Pro",
        PlanType.CONSULTANT: "Consultant",
        PlanType.ENTERPRISE: "Enterprise"
    }
    return names.get(plan, plan.value)

def get_plan_description(plan: PlanType) -> str:
    """Get plan description for display"""
    descriptions = {
        PlanType.FREE: "Free to list properties on marketplace",
        PlanType.DEV: "Perfect for small development teams",
        PlanType.DEV_PRO: "Enhanced capabilities for growing developers", 
        PlanType.CONSULTANT: "Full-featured solution for planning consultants",
        PlanType.ENTERPRISE: "Custom solution with dedicated infrastructure"
    }
    return descriptions.get(plan, "")

# Export key classes and functions
__all__ = [
    "PlanType", 
    "CreditType", 
    "PlanLimits", 
    "PlanPricing", 
    "CreditPack",
    "PricingConfig", 
    "QuotaManager",
    "format_price_display",
    "get_plan_display_name", 
    "get_plan_description"
]